import calendar
import math
from datetime import timedelta, datetime
from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Trabajador, Turno, ReglaEmpresa
from app.scheduler.builder import build_model
from app.scheduler.solver import solve_model
from app.scheduler.explain import extract_solution
from app.scheduler.conflict import get_conflict_report
from ortools.sat.python import cp_model

planificacion_bp = Blueprint('planificacion', __name__, url_prefix='/planificacion')


def _calcular_horas_turno(hora_inicio, hora_fin):
    """
    Calcula la duración en horas de un turno.
    Maneja el caso que cruza medianoche (fin <= inicio).
    hora_inicio y hora_fin son objetos datetime.time.
    """
    h_ini = hora_inicio.hour * 60 + hora_inicio.minute
    h_fin = hora_fin.hour   * 60 + hora_fin.minute
    if h_fin <= h_ini:
        h_fin += 24 * 60
    return (h_fin - h_ini) / 60


def _calcular_es_nocturno(hora_inicio, hora_fin):
    """
    Determina si un turno es nocturno (cruza medianoche).
    Si el campo es_nocturno ya existe en el modelo se usa ese,
    si no se calcula desde hora_inicio/hora_fin.
    """
    return hora_fin <= hora_inicio


@planificacion_bp.route('/generar', methods=['POST'])
def generar():
    data = request.json
    mes        = int(data.get('mes', 0))
    anio       = int(data.get('anio', 0))
    servicio_id = data.get('sucursal_id')

    if not mes or not anio or not servicio_id:
        return jsonify({'status': 'error',
                        'message': 'Faltan parámetros básicos (mes, anio, sucursal).'}), 400

    # ── Trabajadores del servicio ─────────────────────────────────────────────
    trabajadores_db = Trabajador.query.filter_by(
        servicio_id=servicio_id, activo=True
    ).all()
    if not trabajadores_db:
        return jsonify({'status': 'error',
                        'message': 'No hay trabajadores activos en este servicio.'}), 400

    t_ids   = [t.id for t in trabajadores_db]
    t_dicts = [{'id': t.id, 'nombre': f"{t.nombre} {t.apellido1}"}
               for t in trabajadores_db]

    # Empresa se obtiene del primer trabajador (todos pertenecen a la misma)
    empresa_id = trabajadores_db[0].empresa_id

    # ── Turnos de la empresa (no todos del sistema) ───────────────────────────
    turnos_db = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    if not turnos_db:
        return jsonify({'status': 'error',
                        'message': 'No hay turnos activos configurados para esta empresa.'}), 400

    # Abreviaciones únicas manteniendo el orden de BD
    vistas = set()
    turnos_ordenados = []
    for t in turnos_db:
        if t.abreviacion not in vistas:
            turnos_ordenados.append(t)
            vistas.add(t.abreviacion)
    turnos = [t.abreviacion for t in turnos_ordenados]

    # ── turnos_meta: atributos que necesita el builder ────────────────────────
    # es_nocturno: usa campo BD si existe, sino calcula desde horario
    # horas:       calcula desde hora_inicio / hora_fin
    turnos_meta = {}
    for t in turnos_ordenados:
        es_noc = (
            t.es_nocturno
            if hasattr(t, 'es_nocturno') and t.es_nocturno is not None
            else _calcular_es_nocturno(t.hora_inicio, t.hora_fin)
        )
        turnos_meta[t.abreviacion] = {
            'es_nocturno': es_noc,
            'horas':       _calcular_horas_turno(t.hora_inicio, t.hora_fin),
        }

    # Colores para el frontend
    turnos_info = [
        {
            'abreviacion':   t.abreviacion,
            'nombre':        t.nombre,
            'color':         t.color,
            'dotacion_diaria': t.dotacion_diaria,
            'es_nocturno':   turnos_meta[t.abreviacion]['es_nocturno'],
        }
        for t in turnos_ordenados
    ]

    # ── Días del mes ──────────────────────────────────────────────────────────
    num_days    = calendar.monthrange(anio, mes)[1]
    dias_del_mes = []
    dias_dict    = []
    dias_nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    dias_set     = set()  # para búsqueda O(1) en ausencias

    for i in range(1, num_days + 1):
        fecha_str = f"{anio}-{str(mes).zfill(2)}-{str(i).zfill(2)}"
        dias_del_mes.append(fecha_str)
        dias_set.add(fecha_str)
        dia_idx = calendar.weekday(anio, mes, i)
        js_day  = 0 if dia_idx == 6 else dia_idx + 1
        dias_dict.append({
            'fecha':      fecha_str,
            'dia_semana': js_day,
            'label':      f"{str(i).zfill(2)} {dias_nombres[dia_idx]}"
        })

    # ── Coberturas por día ────────────────────────────────────────────────────
    # El usuario puede modificar la dotación por turno antes de generar.
    # La cobertura de domingo puede ser distinta a la global.
    cob_global  = {}
    cob_domingo = {}
    for t in turnos:
        val_g = data.get(f'cob_{t}', 0)
        cob_global[t] = int(val_g) if val_g else 0

        val_s = data.get(f'cob_sun_{t}')
        cob_domingo[t] = int(val_s) if (val_s is not None and val_s != '') else cob_global[t]

    coberturas_por_dia = {}
    for d_str in dias_del_mes:
        py_date = datetime.strptime(d_str, '%Y-%m-%d').date()
        coberturas_por_dia[d_str] = cob_domingo if py_date.weekday() == 6 else cob_global

    # ── trabajadores_meta ─────────────────────────────────────────────────────
    # duracion_turno: calculada desde los turnos reales del trabajador
    #   solo_turno → duración de esos turnos específicos
    #   sin restricción → promedio de todos los turnos de la empresa
    # permite_horas_extra: desde campo BD del trabajador (default False)
    trabajadores_meta = {}
    for t in trabajadores_db:
        if getattr(t, '_turnos_solo', None):
            horas_w = [turnos_meta[abr]['horas']
                       for abr in t._turnos_solo
                       if abr in turnos_meta]
        else:
            horas_w = [v['horas'] for v in turnos_meta.values()]

        duracion_w = round(sum(horas_w) / len(horas_w)) if horas_w else 8

        trabajadores_meta[t.id] = {
            'horas_semanales':     t.horas_semanales or None,
            'turnos_permitidos':   getattr(t, '_turnos_solo', None),
            'duracion_turno':      duracion_w,
            'permite_horas_extra': getattr(t, 'permite_horas_extra', False) or False,
        }

    # ── Reglas de la empresa desde BD ────────────────────────────────────────
    reglas_bd = {}
    reglas_empresa = ReglaEmpresa.query.filter_by(
        empresa_id=empresa_id, activo=True
    ).all()
    for re in reglas_empresa:
        codigo = re.regla_rel.codigo
        params = re.params_custom if re.params_custom else re.regla_rel.params_base
        if not params:
            continue
        if codigo == 'working_days_limit':
            reglas_bd['working_days_limit_min'] = params.get('min', 5)
            reglas_bd['working_days_limit_max'] = params.get('max', 6)
        elif codigo == 'min_free_sundays':
            reglas_bd['min_free_sundays'] = params.get('value', 2)
        elif codigo == 'dias_descanso_post_6':
            reglas_bd['dias_descanso_post_6'] = params.get('value', 1)
        elif codigo == 'jornada_semanal':
            reglas_bd['jornada_semanal'] = params.get('value', 42)
        elif codigo == 'duracion_turno':
            reglas_bd['duracion_turno'] = params.get('value', 8)

    # Calcular duracion_turno promedio desde los turnos reales si no viene en reglas
    if 'duracion_turno' not in reglas_bd and turnos_meta:
        horas_lista = [v['horas'] for v in turnos_meta.values()]
        reglas_bd['duracion_turno'] = round(sum(horas_lista) / len(horas_lista))

    # ── Ausencias ─────────────────────────────────────────────────────────────
    ausencias = {}
    for t in trabajadores_db:
        for a in t.ausencias:
            if not a.fecha_inicio or not a.fecha_fin:
                continue
            curr = a.fecha_inicio
            while curr <= a.fecha_fin:
                f_str = curr.strftime('%Y-%m-%d')
                if f_str in dias_set:
                    abr = a.tipo_ausencia.abreviacion if a.tipo_ausencia else 'A'
                    ausencias[(t.id, f_str)] = abr
                curr += timedelta(days=1)

    # ── Pre-procesamiento: bloqueados, fijos y preferencias diarias ──────────
    from app.scheduler.builder import preparar_restricciones
    bloqueados, fijos, turnos_bloqueados_por_dia = preparar_restricciones(
        trabajadores_db, dias_del_mes, ausencias
    )

    # ── Construir y resolver el modelo ────────────────────────────────────────
    try:
        model, x = build_model(
            t_ids,
            dias_del_mes,
            turnos,
            coberturas_por_dia,
            bloqueados,
            fijos,
            turnos_bloqueados_por_dia=turnos_bloqueados_por_dia,
            reglas=reglas_bd,
            trabajadores_meta=trabajadores_meta,
            turnos_meta=turnos_meta,
        )
        solver, status = solve_model(model)

        from ortools.sat.python import cp_model as _cp
        print(f"\n{'='*50}")
        print(f"STATUS: {['UNKNOWN','MODEL_INVALID','FEASIBLE','INFEASIBLE','OPTIMAL'][status]}")
        print(f"Trabajadores: {len(t_ids)}")
        print(f"Turnos: {turnos}")
        print(f"Bloqueados: {len(bloqueados)}")
        print(f"Fijos: {len(fijos)}")
        print(f"reglas_bd: {reglas_bd}")
        print(f"turnos_meta: {turnos_meta}")
        for w, meta in trabajadores_meta.items():
            print(f"  Worker {w}: {meta}")
        print(f"{'='*50}\n")

        # ── DEBUG TEMPORAL ────────────────────────────────────────────
        from collections import Counter
        import math
        bloq_por_worker = Counter(w for (w, d) in bloqueados)
        print(f"\n[BLOQUEADOS Y META REAL por worker]")
        for w in t_ids:
            b    = bloq_por_worker.get(w, 0)
            meta = trabajadores_meta.get(w, {})
            h    = meta.get('horas_semanales', 42)
            dur  = meta.get('duracion_turno', 8)
            ext  = meta.get('permite_horas_extra', False)
            disp = 31 - b   # ← cambia 31 por el num_days real si quieres
            raw  = disp / 7 * (h / dur)
            m    = math.ceil(raw) if ext else math.floor(raw)
            print(f"  Worker {w}: bloq={b} disp={disp} raw={raw:.2f} meta={m} extra={ext}")
        print('='*50)
        # ── FIN DEBUG ─────────────────────────────────────────────────

        # UNKNOWN = timeout → error bloqueante, no hay nada que mostrar
        if status == cp_model.UNKNOWN:
            conflict_report = get_conflict_report(status)
            return jsonify({
                'status': 'error',
                'message': conflict_report['message']
            }), 400

        # OPTIMAL / FEASIBLE → solución completa
        # INFEASIBLE          → matriz vacía, el usuario completa manualmente
        advertencia = None
        if status == cp_model.INFEASIBLE:
            conflict_report = get_conflict_report(status)
            advertencia = conflict_report['message'] if conflict_report else (
                'No fue posible resolver el cuadrante automáticamente. '
                'Puede completarlo manualmente.'
            )

        celdas = extract_solution(
            solver, status, x, t_ids, dias_del_mes, turnos, ausencias
        )

        # Métricas de cobertura (solo cuenta turnos reales, no L ni vacíos)
        turnos_necesarios = sum(
            v for c in coberturas_por_dia.values()
            for v in c.values()
            if isinstance(v, int)
        )

        return jsonify({
            'status': 'ok',
            'data': {
                'dias':          dias_dict,
                'trabajadores':  t_dicts,
                'celdas':        celdas,
                'turnos':        turnos_info,   # colores y metadatos para el frontend
                'estado':        'simulacion',
                'advertencia':   advertencia,   # None si todo ok, mensaje si INFEASIBLE
                'metricas': {
                    'necesarios': turnos_necesarios
                }
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error en el motor CP-SAT: {str(e)}'
        }), 500


@planificacion_bp.route('/celda', methods=['POST'])
def update_celda():
    # En modo simulación solo confirmamos el cambio.
    # La persistencia real ocurre al publicar.
    return jsonify({'status': 'ok'})


@planificacion_bp.route('/publicar', methods=['POST'])
def publicar():
    # Aquí irá la lógica para guardar el cuadrante oficial en BD.
    return jsonify({'status': 'ok', 'message': 'El cuadrante ha sido publicado.'})

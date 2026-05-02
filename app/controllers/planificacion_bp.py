import calendar
import math
from datetime import timedelta, datetime
from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Trabajador, Turno, ReglaEmpresa, TrabajadorRestriccionTurno
from app.scheduler.builder import build_model
from app.scheduler.solver import solve_model
from app.scheduler.explain import extract_solution
from app.scheduler.conflict import get_conflict_report
from flask_login import login_required, current_user
from app.services.context import get_empresa_activa_id, usuario_tiene_acceso
from ortools.sat.python import cp_model
import logging

planificacion_bp = Blueprint('planificacion', __name__, url_prefix='/planificacion')
logger = logging.getLogger(__name__)


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
@login_required
def generar():
    data = request.json
    mes        = int(data.get('mes', 0))
    anio       = int(data.get('anio', 0))
    servicio_id = data.get('sucursal_id')

    if not mes or not anio or not servicio_id:
        return jsonify({'status': 'error',
                        'message': 'Faltan parámetros básicos (mes, anio, sucursal).'}), 400

    # 1. Validaciones de Integridad
    from app.models.business import ParametroLegal
    
    # Verificar Parámetros Legales Globales
    params_count = ParametroLegal.query.filter_by(es_activo=True).count()
    if params_count == 0:
        return jsonify({'status': 'error', 
                        'message': 'No se encontraron Parámetros Legales configurados en el sistema.'}), 400

    empresa_id_activa = get_empresa_activa_id()
    
    # Verificar Trabajadores
    trabajadores_db = Trabajador.query.filter_by(
        empresa_id=empresa_id_activa,
        servicio_id=servicio_id, 
        activo=True
    ).all()
    if not trabajadores_db:
        return jsonify({'status': 'error',
                        'message': 'No hay trabajadores activos en este servicio. Por favor, asigne personal antes de generar.'}), 400

    # Verificar Turnos
    turnos_db = Turno.query.filter_by(empresa_id=empresa_id_activa, activo=True).all()
    if not turnos_db:
        return jsonify({'status': 'error',
                        'message': 'La empresa no tiene turnos configurados o activos.'}), 400

    t_ids   = [t.id for t in trabajadores_db]
    t_dicts = [{'id': t.id, 'nombre': f"{t.nombre} {t.apellido1}"}
               for t in trabajadores_db]

    # Empresa se obtiene del primer trabajador (todos pertenecen a la misma)
    empresa_id = trabajadores_db[0].empresa_id
    
    # Validar que el usuario tiene acceso a esta empresa
    if not usuario_tiene_acceso(current_user, empresa_id):
        return jsonify({'status': 'error', 'message': 'Sin acceso a esta empresa.'}), 403

    # ── Turnos de la empresa (no todos del sistema) ───────────────────────────
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
        dia_idx = calendar.weekday(anio, mes, i)  # 0=Lun, 6=Dom (Python)
        dias_dict.append({
            'fecha':      fecha_str,
            'dia_semana': dia_idx,   # JS render usa 6=Dom (igual que Python weekday)
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

    # ── Ausencias (Bloqueos de día completo) ──────────────────────────────────
    ausencias = {}
    for t in trabajadores_db:
        for a in t.ausencias:
            if not a.fecha_inicio or not a.fecha_fin:
                continue
            
            # SGT 2.1: Solo considerar ausencias que bloquean el día completo (Vacaciones, Licencias, etc.)
            # Las restricciones de turno se procesan por separado a través de restricciones_especiales
            if not a.es_bloqueo_dia:
                continue

            curr = a.fecha_inicio
            while curr <= a.fecha_fin:
                f_str = curr.strftime('%Y-%m-%d')
                if f_str in dias_set:
                    abr = a.tipo_ausencia.abreviacion if a.tipo_ausencia else 'A'
                    ausencias[(t.id, f_str)] = abr
                curr += timedelta(days=1)

    # ── Restricciones Especiales SGT 2.1 ─────────────────────────────────────
    fecha_ini_periodo = datetime.strptime(dias_del_mes[0], '%Y-%m-%d').date()
    fecha_fin_periodo = datetime.strptime(dias_del_mes[-1], '%Y-%m-%d').date()
    restricciones_especiales = TrabajadorRestriccionTurno.query.filter(
        TrabajadorRestriccionTurno.trabajador_id.in_(t_ids),
        TrabajadorRestriccionTurno.fecha_inicio <= fecha_fin_periodo,
        TrabajadorRestriccionTurno.fecha_fin >= fecha_ini_periodo,
        TrabajadorRestriccionTurno.activo == True
    ).all()

    # ── Pre-procesamiento: bloqueados, fijos y preferencias ─────────────────
    from app.scheduler.builder import preparar_restricciones
    bloqueados, fijos, turnos_bloqueados_por_dia, r_hard, r_soft = preparar_restricciones(
        trabajadores_db, dias_del_mes, ausencias, restricciones_especiales
    )

    # ── trabajadores_meta ─────────────────────────────────────────────────────
    # duracion_turno: calculada desde los turnos reales del trabajador
    #   solo_turno → duración de esos turnos específicos (t._turnos_solo)
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
            'horas_semanales':     t.horas_semanales if t.horas_semanales else 42.0,
            'tipo_contrato':       t.tipo_contrato.name if t.tipo_contrato else 'FULL_TIME',
            'turnos_permitidos':   getattr(t, '_turnos_solo', None),
            'duracion_turno':      duracion_w,
            'permite_horas_extra': getattr(t, 'permite_horas_extra', False) or False,
        }

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
            restricciones_hard=r_hard,
            restricciones_soft=r_soft,
            reglas=reglas_bd,
            trabajadores_meta=trabajadores_meta,
            turnos_meta=turnos_meta,
        )
        solver, status = solve_model(model)

        from ortools.sat.python import cp_model as _cp
        import math as _math
        _STATUS = ['UNKNOWN','MODEL_INVALID','FEASIBLE','INFEASIBLE','OPTIMAL']
        logger.info(f"--- SOLVER STATUS: {_STATUS[status]} ---")
        logger.info(f"Trabajadores: {len(t_ids)} | Turnos: {turnos}")
        logger.info(f"Bloqueados: {len(bloqueados)} | Fijos: {len(fijos)}")
        logger.info(f"Reglas: {reglas_bd}")
        
        _min_dom = reglas_bd.get('min_free_sundays', 1)
        for w, meta in trabajadores_meta.items():
            h    = meta.get('horas_semanales', 42) or 42
            dur  = meta.get('duracion_turno', 8) or 8
            ext  = meta.get('permite_horas_extra', False)
            bloq = sum(1 for (ww, d) in bloqueados if ww == w)
            dom_bloq = sum(1 for (ww, d) in bloqueados
                          if ww == w and
                          calendar.weekday(int(d[:4]),int(d[5:7]),int(d[8:10])) == 6)
            dom_lib  = max(0, _min_dom - dom_bloq)
            disp     = num_days - bloq - dom_lib
            raw      = disp / 7 * (h / dur)
            meta_cal = _math.ceil(raw) if ext else _math.floor(raw)
            logger.info(f"  Worker {w}: {h}h dur={dur} meta={meta_cal}")

        if fijos:
            logger.info(f"Fijos por worker: {len(fijos)} registros.")

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

        # ── Debug post-solución ───────────────────────────────────────────────
        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            print(f"\n[SGT] TOTALES POR WORKER Y TURNO:")
            total_general = 0
            for w in t_ids:
                nombre = next((t['nombre'] for t in t_dicts if t['id'] == w), str(w))
                total_w = sum(
                    1 for d in dias_del_mes for t in turnos
                    if solver.Value(x[w, d, t]) == 1
                )
                por_turno = {
                    t: sum(1 for d in dias_del_mes if solver.Value(x[w, d, t]) == 1)
                    for t in turnos
                }
                meta_w = trabajadores_meta.get(w, {})
                h      = meta_w.get('horas_semanales', 42) or 42
                dur    = meta_w.get('duracion_turno', 8) or 8
                ext    = meta_w.get('permite_horas_extra', False)
                alerta = " ⚠️ SOBRE META" if total_w > _math.ceil(h/dur * num_days/7) else ""
                print(f"  {nombre[:20]:<20} total={total_w:>3} {por_turno}{alerta}")
                total_general += total_w
            print(f"  {'TOTAL GENERAL':<20} {total_general}")

            print(f"\n[SGT] COBERTURA POR TURNO:")
            for t in turnos:
                req_total  = sum(coberturas_por_dia[d].get(t, 0) for d in dias_del_mes)
                real_total = sum(
                    1 for d in dias_del_mes
                    for w in t_ids
                    if solver.Value(x[w, d, t]) == 1
                )
                diff = real_total - req_total
                estado = "✅" if diff == 0 else ("⚠️ SUPERÁVIT" if diff > 0 else "❌ DÉFICIT")
                print(f"  Turno {t}: req={req_total} real={real_total} diff={diff:+} {estado}")
            print(f"{'='*60}\n")

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


@planificacion_bp.route('/generar_stream')
@login_required
def generar_stream():
    from flask import Response, stream_with_context
    import json
    import time

    def event_stream():
        try:
            # 1. Preparación de Parámetros
            yield f"event: log\ndata: {json.dumps({'msg': 'Analizando parámetros...', 'progress': 5, 'status': 'Preparando...'})}\n\n"
            time.sleep(0.5)

            mes = int(request.args.get('mes', 0))
            anio = int(request.args.get('anio', 0))
            servicio_id = request.args.get('sucursal_id')

            if not mes or not anio or not servicio_id:
                yield f"event: error_sgt\ndata: {json.dumps({'message': 'Faltan parámetros básicos.'})}\n\n"
                return

            # 2. Carga de Datos (Filtrado por Empresa y Servicio)
            yield f"event: log\ndata: {json.dumps({'msg': 'Cargando dotación y contratos...', 'progress': 15, 'status': 'Cargando datos...'})}\n\n"
            
            _, num_days = calendar.monthrange(anio, mes)
            
            emp_id_stream = get_empresa_activa_id()
            trabajadores_db = Trabajador.query.filter_by(
                empresa_id=emp_id_stream,
                servicio_id=servicio_id, 
                activo=True
            ).all()
            if not trabajadores_db:
                yield f"event: error_sgt\ndata: {json.dumps({'message': 'No hay trabajadores activos.'})}\n\n"
                return

            t_dicts = []
            import math
            for t in trabajadores_db:
                # Meta espejo del builder
                max_dias_semana = 6
                if t.tipo_contrato.name == 'PART_TIME':
                    max_dias_semana = min(6, math.ceil(t.horas_semanales / 7.5))
                
                meta_m = math.floor((num_days / 7.0) * max_dias_semana)
                t_dicts.append({
                    'id': t.id, 
                    'nombre': f"{t.nombre} {t.apellido1}",
                    'meta_mensual': meta_m
                })
            turnos_db = Turno.query.filter_by(empresa_id=trabajadores_db[0].empresa_id, activo=True).all()
            
            # 3. Construcción del Modelo
            yield f"event: log\ndata: {json.dumps({'msg': 'Construyendo modelo de planificación...', 'progress': 35, 'status': 'Construyendo...'})}\n\n"
            time.sleep(0.8)
            
            # Recopilar coberturas desde args
            coberturas_raw = {}
            for k, v in request.args.items():
                if k.startswith('cob_'): coberturas_raw[k] = v

            # 4. Invocación al Solver
            yield f"event: log\ndata: {json.dumps({'msg': 'Buscando la mejor combinación de turnos...', 'progress': 50, 'status': 'Optimizando...'})}\n\n"
            
            # --- LÓGICA DE DÍAS Y RESTRICCIONES ---
            dias_mes_objs = [datetime(anio, mes, d).date() for d in range(1, num_days + 1)]
            dias_del_mes = [d.isoformat() for d in dias_mes_objs]
            
            # Coberturas por día
            coberturas_por_dia = {}
            for d_str in dias_del_mes:
                d_obj = datetime.strptime(d_str, '%Y-%m-%d').date()
                es_dom = (d_obj.weekday() == 6)
                key_prefix = 'cob_sun_' if es_dom else 'cob_'
                day_cobs = {}
                for t in turnos_db:
                    val = request.args.get(f"{key_prefix}{t.abreviacion}")
                    if val is None and es_dom: val = request.args.get(f"cob_{t.abreviacion}")
                    day_cobs[t.abreviacion] = int(val) if val else 0
                coberturas_por_dia[d_str] = day_cobs

            # Carga de restricciones especiales y ausencias
            from app.models.business import TrabajadorAusencia, TrabajadorRestriccionTurno
            ausencias_db = TrabajadorAusencia.query.filter(TrabajadorAusencia.trabajador_id.in_([t.id for t in trabajadores_db])).all()
            
            # Expandir rangos de ausencia en días individuales
            ausencias_set = set()
            ausencias_dict = {} # Para extract_solution (Prioridad visual)
            for a in ausencias_db:
                curr_a = a.fecha_inicio
                while curr_a <= a.fecha_fin:
                    d_str = curr_a.isoformat()
                    # Solo bloqueamos el día en el solver si es un bloqueo real (Vacaciones, Licencia, etc.)
                    if a.es_bloqueo_dia:
                        ausencias_set.add((a.trabajador_id, d_str))
                        # Para bloqueos (VAC, LM), mostramos la abreviación del tipo
                        ausencias_dict[(a.trabajador_id, d_str)] = a.tipo_ausencia.abreviacion if a.tipo_ausencia else 'A'
                    
                    # Las restricciones técnicas (Turno Fijo) NO van en ausencias_dict 
                    # para que el solver muestre el turno real asignado (M, T, etc.)
                    
                    curr_a += timedelta(days=1)
            
            restricciones_especiales = TrabajadorRestriccionTurno.query.filter(
                TrabajadorRestriccionTurno.trabajador_id.in_([t.id for t in trabajadores_db]),
                TrabajadorRestriccionTurno.activo == True
            ).all()

            # Preparar bloques y fijos
            from app.scheduler.builder import preparar_restricciones
            bloqueados, fijos, turnos_bloqueados, res_hard, res_soft = preparar_restricciones(
                trabajadores_db, dias_del_mes, ausencias_set, restricciones_especiales
            )

            # Metadatos para el solver
            trabajadores_meta = {t.id: {
                'tipo_contrato': t.tipo_contrato,
                'horas_semanales': t.horas_semanales,
                'permite_horas_extra': t.permite_horas_extra
            } for t in trabajadores_db}
            
            turnos_meta = {t.abreviacion: {
                'horas': t.duracion_hrs,
                'es_nocturno': t.es_nocturno,
                'nombre': t.nombre
            } for t in turnos_db}

            yield f"event: log\ndata: {json.dumps({'msg': 'Validando cumplimiento de Ley 21.561...', 'progress': 75, 'status': 'Construyendo...'})}\n\n"
            
            # Llamada al builder corregida
            model, variables = build_model(
                trabajadores=[t.id for t in trabajadores_db],
                dias_del_mes=dias_del_mes,
                turnos=[t.abreviacion for t in turnos_db],
                coberturas=coberturas_por_dia,
                bloqueados=bloqueados,
                fijos=fijos,
                turnos_bloqueados_por_dia=turnos_bloqueados,
                restricciones_hard=res_hard,
                restricciones_soft=res_soft,
                trabajadores_meta=trabajadores_meta,
                turnos_meta=turnos_meta
            )
            
            yield f"event: log\ndata: {json.dumps({'msg': 'Buscando solución óptima...', 'progress': 85, 'status': 'Resolviendo...'})}\n\n"
            
            # Llamada al solver
            solver, status = solve_model(model)

            if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
                yield f"event: log\ndata: {json.dumps({'msg': '¡Planificación optimizada con éxito!', 'type': 'success', 'progress': 95, 'status': 'Finalizando...'})}\n\n"
                celdas = extract_solution(solver, status, variables, [t.id for t in trabajadores_db], dias_del_mes, [t.abreviacion for t in turnos_db], ausencias_dict)
                
                # Formatear respuesta final
                dias_dict = []
                DIAS_SEM = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for i, d_str in enumerate(dias_del_mes):
                    d_obj = dias_mes_objs[i]
                    dias_dict.append({'fecha': d_str, 'dia_semana': d_obj.weekday(), 'label': f"{d_obj.day:02d} {DIAS_SEM[d_obj.weekday()]}"})
                
                turnos_info = {t.abreviacion: {'color': t.color, 'nombre': t.nombre} for t in turnos_db}
                turnos_necesarios = sum(v for c in coberturas_por_dia.values() for v in c.values() if isinstance(v, int))

                result_data = {
                    'dias': dias_dict,
                    'trabajadores': t_dicts,
                    'celdas': celdas,
                    'turnos': turnos_info,
                    'estado': 'simulacion',
                    'metricas': {'necesarios': turnos_necesarios}
                }
                
                yield f"event: result\ndata: {json.dumps({'data': result_data})}\n\n"
            else:
                yield f"event: error_sgt\ndata: {json.dumps({'message': 'No se pudo encontrar una solución válida (INFEASIBLE).'})}\n\n"

        except Exception as e:
            yield f"event: error_sgt\ndata: {json.dumps({'message': str(e)})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')


@planificacion_bp.route('/celda', methods=['POST'])
def update_celda():
    return jsonify({'status': 'ok'})


@planificacion_bp.route('/publicar', methods=['POST'])
def publicar():
    return jsonify({'status': 'ok', 'message': 'El cuadrante ha sido publicado.'})

@planificacion_bp.route('/editar/<int:cabecera_id>')
@login_required
def editar(cabecera_id):
    return _render_plan_db(cabecera_id, modo='editar')

@planificacion_bp.route('/ver/<int:cabecera_id>')
@login_required
def ver(cabecera_id):
    return _render_plan_db(cabecera_id, modo='ver')

def _render_plan_db(cabecera_id, modo='ver'):
    from app.models.scheduling import CuadranteCabecera
    from app.models.business import Empresa, Servicio, Turno, Trabajador, TipoAusencia
    cabecera = CuadranteCabecera.query.get_or_404(cabecera_id)
    empresa_id = cabecera.empresa_id
    
    # Validar que el usuario tiene acceso a esta empresa
    if not usuario_tiene_acceso(current_user, empresa_id):
        return jsonify({'status': 'error', 'message': 'Sin acceso a esta empresa.'}), 403

    servicios = Servicio.query.join(Servicio.empresas_asociadas).filter(Empresa.id == empresa_id, Servicio.activo == True).all()
    turnos = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    tipos_ausencia = TipoAusencia.query.filter_by(empresa_id=empresa_id, activo=True).all()
    
    # Feriados del mes guardado
    import calendar
    from app.models.core import Feriado
    _, last_day = calendar.monthrange(cabecera.anio, cabecera.mes)
    start_date = datetime(cabecera.anio, cabecera.mes, 1).date()
    end_date = datetime(cabecera.anio, cabecera.mes, last_day).date()
    feriados_del_mes = Feriado.query.filter(Feriado.fecha >= start_date, Feriado.fecha <= end_date, Feriado.activo == True).all()
    feriados_dict = {
        f.fecha.strftime('%Y-%m-%d'): {
            'es_irrenunciable': f.es_irrenunciable,
            'es_regional': f.es_regional,
            'tipo_display': f.tipo_display,
            'badge_config': f.badge_config
        } for f in feriados_del_mes
    }
    
    empresa_activa = Empresa.query.get(empresa_id)
    
    # Cargar Asignaciones
    from sqlalchemy.orm import joinedload
    from app.models.scheduling import CuadranteAsignacion
    asignaciones = cabecera.asignaciones.options(joinedload(CuadranteAsignacion.turno), joinedload(CuadranteAsignacion.trabajador)).all()
    
    celdas = {}
    for a in asignaciones:
        f_str = a.fecha.strftime('%Y-%m-%d')
        if f_str not in celdas:
            celdas[f_str] = {}
        
        abr = 'L'
        if not a.es_libre and a.turno:
            abr = a.turno.abreviacion
            
        celdas[f_str][a.trabajador_id] = {
            'abr': abr,
            'origen': a.origen
        }
            
    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, servicio_id=cabecera.servicio_id, activo=True).all()
    t_dicts = []
    import math
    for t in trabajadores:
        # Lógica espejo del builder.py para cálculo de meta
        # max_dias_semana depende del tipo de contrato (FULL=6, PART=variable pero usualmente usamos 6 como base legal max)
        max_dias_semana = 6 
        if t.tipo_contrato.name == 'PART_TIME':
            # Si es part-time, la meta es proporcional a sus horas (ej 30h / 8h turno = 3.75 -> 4 días)
            max_dias_semana = min(6, math.ceil(t.horas_semanales / 7.5))
            
        # Días disponibles en el mes (restando bloqueos/ausencias grabadas)
        # Por simplicidad en el render, usamos el total de días del mes como base, 
        # el builder es más fino pero esto da una meta teórica correcta.
        meta_m = math.floor((last_day / 7.0) * max_dias_semana)
        
        t_dicts.append({
            'id': t.id, 
            'nombre': f"{t.nombre} {t.apellido1}",
            'meta_mensual': meta_m
        })
    
    dias_dict = []
    dias_nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    for i in range(1, last_day + 1):
        fecha_str = f"{cabecera.anio}-{str(cabecera.mes).zfill(2)}-{str(i).zfill(2)}"
        dia_idx = calendar.weekday(cabecera.anio, cabecera.mes, i)
        dias_dict.append({
            'fecha': fecha_str,
            'dia_semana': dia_idx,
            'label': f"{str(i).zfill(2)} {dias_nombres[dia_idx]}"
        })
        
    turnos_info = [{'abreviacion': t.abreviacion, 'nombre': t.nombre, 'color': t.color, 'duracion': float(t.duracion_hrs)} for t in turnos]

    import json
    preloaded_data = {
        'dias': dias_dict,
        'trabajadores': t_dicts,
        'celdas': celdas,
        'turnos': turnos_info,
        'estado': cabecera.estado,
        'metricas': {'necesarios': 0}
    }

    return render_template('simulacion.html', 
                           servicios=servicios, 
                           turnos=turnos, 
                           tipos_ausencia=tipos_ausencia, 
                           current_year=cabecera.anio, 
                           current_month=cabecera.mes,
                           feriados_dict=feriados_dict,
                           empresa_activa=empresa_activa,
                           modo=modo,
                           cabecera_id=cabecera_id,
                           preloaded_data=json.dumps(preloaded_data))

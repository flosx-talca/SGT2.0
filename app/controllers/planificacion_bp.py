import calendar
from datetime import date
from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Trabajador, Turno, Servicio, ReglaEmpresa
from app.scheduler.builder import build_model
from app.scheduler.solver import solve_model
from app.scheduler.explain import extract_solution
from app.scheduler.conflict import get_conflict_report
from ortools.sat.python import cp_model

planificacion_bp = Blueprint('planificacion', __name__, url_prefix='/planificacion')

@planificacion_bp.route('/generar', methods=['POST'])
def generar():
    data = request.json
    mes = int(data.get('mes', 0))
    anio = int(data.get('anio', 0))
    servicio_id = data.get('sucursal_id') # Es servicio_id en la BD
    
    if not mes or not anio or not servicio_id:
        return jsonify({'status': 'error', 'message': 'Faltan parámetros básicos (mes, anio, sucursal).'}), 400
        
    # Obtener trabajadores del servicio
    trabajadores_db = Trabajador.query.filter_by(servicio_id=servicio_id, activo=True).all()
    if not trabajadores_db:
        return jsonify({'status': 'error', 'message': 'No hay trabajadores activos en este servicio.'}), 400
        
    # Extraer IDs
    t_ids = [t.id for t in trabajadores_db]
    t_dicts = [{'id': t.id, 'nombre': f"{t.nombre} {t.apellido1}"} for t in trabajadores_db]
    
    # Obtener turnos
    turnos_db = Turno.query.filter_by(activo=True).all()
    turnos = list(set([t.abreviacion for t in turnos_db])) # Eliminar duplicados
    if not turnos:
        return jsonify({'status': 'error', 'message': 'No existen turnos activos configurados en el sistema. Por favor, configure los turnos en el mantenedor.'}), 400
        
    # Generar días del mes
    num_days = calendar.monthrange(anio, mes)[1]
    dias_del_mes = []
    dias_dict = []
    dias_nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    for i in range(1, num_days + 1):
        fecha_str = f"{anio}-{str(mes).zfill(2)}-{str(i).zfill(2)}"
        dias_del_mes.append(fecha_str)
        dia_idx = calendar.weekday(anio, mes, i)
        # JS expects dia_semana to be 0=Dom, 1=Lun, ..., 6=Sab. Python calendar: 0=Lun, 6=Dom
        js_day = 0 if dia_idx == 6 else dia_idx + 1
        dias_dict.append({
            "fecha": fecha_str,
            "dia_semana": js_day,
            "label": f"{str(i).zfill(2)} {dias_nombres[dia_idx]}"
        })
        
    # Coberturas (dinámicas basadas en los turnos de BD)
    coberturas = {}
    for t in turnos:
        # Busca el input cob_{abreviacion} (ej: cob_M, cob_T)
        val = data.get(f'cob_{t}', 0)
        coberturas[t] = int(val) if val else 0
    
    # Extraer metadatos de trabajadores (tipo contrato, horas)
    trabajadores_meta = {
        t.id: {
            'tipo_contrato':  t.tipo_contrato,
            'horas_semanales': t.horas_semanales or 45
        }
        for t in trabajadores_db
    }
    
    # Leer reglas de empresa de la BD
    # Asumimos que el servicio pertenece a una empresa - usamos la primera empresa del 1er trabajador
    reglas_bd = {}
    if trabajadores_db:
        empresa_id = trabajadores_db[0].empresa_id
        reglas_empresa = ReglaEmpresa.query.filter_by(empresa_id=empresa_id, activo=True).all()
        for re in reglas_empresa:
            codigo = re.regla_rel.codigo
            # Usar params_custom si existe, sino params_base de la regla maestra
            params = re.params_custom if re.params_custom else re.regla_rel.params_base
            if codigo == 'working_days_limit' and params:
                reglas_bd['working_days_limit_min'] = params.get('min', 5)
                reglas_bd['working_days_limit_max'] = params.get('max', 6)
            elif codigo == 'min_free_sundays' and params:
                reglas_bd['min_free_sundays'] = params.get('value', 2)
    
    # Extraer ausencias y preferencias
    ausencias = {}
    preferencias = {}
    for t in trabajadores_db:
        # Ausencias
        for a in t.ausencias:
            f_ini = a.fecha_inicio
            f_fin = a.fecha_fin
            # Marcar días en el rango si caen en el mes actual
            if f_ini and f_fin:
                d = f_ini
                while d <= f_fin:
                    f_str = d.strftime('%Y-%m-%d')
                    if f_str in dias_del_mes:
                        ausencias[(t.id, f_str)] = a.tipo_ausencia.abreviacion if a.tipo_ausencia else "A"
                    from datetime import timedelta
                    d += timedelta(days=1)
                    
        # Preferencias
        for p in t.preferencias:
            # p.dia_semana (0=Lunes, 6=Domingo)
            # Aplicar preferencia a todos los días del mes que coincidan con ese día de la semana
            for dia_str, dia_obj in zip(dias_del_mes, dias_dict):
                # Python calendar weekday
                py_weekday = calendar.weekday(int(dia_str[0:4]), int(dia_str[5:7]), int(dia_str[8:10]))
                if p.dia_semana == py_weekday:
                    preferencias[(t.id, dia_str)] = p.turno

    # Construir y resolver el modelo
    try:
        model, x = build_model(
            t_ids, dias_del_mes, turnos, coberturas, ausencias, preferencias,
            reglas=reglas_bd,
            trabajadores_meta=trabajadores_meta
        )
        solver, status = solve_model(model)
        
        # Ya no bloqueamos por INFEASIBLE: el modelo es 100% Soft, siempre hay solución.
        # Solo advertimos si el solver no pudo hacer nada en absoluto (UNKNOWN).
        advertencia = None
        conflict_report = get_conflict_report(status)
        if conflict_report and status == cp_model.UNKNOWN:
            return jsonify({'status': 'error', 'message': conflict_report['message']}), 400
            
        celdas = extract_solution(solver, status, x, t_ids, dias_del_mes, turnos, ausencias)
        
        # Calcular métricas básicas
        turnos_necesarios = sum(coberturas.values()) * len(dias_del_mes)
        
        return jsonify({
            'status': 'ok',
            'data': {
                'dias': dias_dict,
                'trabajadores': t_dicts,
                'celdas': celdas,
                'estado': 'simulacion',
                'metricas': {
                    'necesarios': turnos_necesarios
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error en el motor CP-SAT: {str(e)}'}), 500

@planificacion_bp.route('/celda', methods=['POST'])
def update_celda():
    # Este endpoint solo devuelve OK si estamos en modo simulación
    # ya que no guardaremos en BD hasta que publiquen.
    return jsonify({'status': 'ok'})

@planificacion_bp.route('/publicar', methods=['POST'])
def publicar():
    # Aquí irá la lógica para guardar el cuadrante oficial.
    return jsonify({'status': 'ok', 'message': 'El cuadrante ha sido publicado.'})

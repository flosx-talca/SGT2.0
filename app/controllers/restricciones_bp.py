from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.context import get_empresa_activa_id, usuario_tiene_acceso
from app.database import db
from app.models.business import Trabajador, TrabajadorRestriccionTurno, Turno, TrabajadorAusencia, TipoAusencia
from app.models.enums import RestrictionType, NATURALEZA_POR_TIPO, CategoriaAusencia
from datetime import datetime

restricciones_bp = Blueprint('restricciones', __name__)

@restricciones_bp.route('/api/restricciones/worker/<int:worker_id>', methods=['GET'])
@login_required
def get_worker_restrictions(worker_id):
    # Validar acceso al trabajador
    worker = db.get_or_404(Trabajador, worker_id)
    if not usuario_tiene_acceso(current_user, worker.empresa_id):
        return jsonify({'status': 'error', 'msg': 'Sin acceso a este trabajador'}), 403
    # Obtener ausencias (bloqueos de día) y restricciones técnicas ordenadas cronológicamente
    ausencias = TrabajadorAusencia.query.filter_by(trabajador_id=worker_id).order_by(TrabajadorAusencia.fecha_inicio.asc()).all()
    
    # Mapear a un formato unificado para la tabla de la UI
    res = []
    for a in ausencias:
        tipo_nombre = a.tipo_ausencia.nombre if a.tipo_ausencia else "Ausencia"
        categoria = a.tipo_ausencia.categoria if a.tipo_ausencia else CategoriaAusencia.AUSENCIA
        
        # Si tiene una restricción técnica asociada, sacar el nombre del turno
        turno_nombre = "-"
        dias_str = "Todos"
        
        if a.restriccion:
            turno_nombre = a.restriccion.turno.nombre if a.restriccion.turno else "N/A"
            dias_semana = a.restriccion.dias_semana
            if dias_semana:
                dias_map = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
                dias_str = ",".join([dias_map[i] for i in dias_semana])

        res.append({
            'id': a.id,
            'tipo': tipo_nombre,
            'categoria': categoria,
            'fecha_inicio': a.fecha_inicio.isoformat(),
            'fecha_fin': a.fecha_fin.isoformat(),
            'dias_semana': dias_str,
            'turno': turno_nombre,
            'motivo': a.motivo
        })
    
    return jsonify(res)

@restricciones_bp.route('/api/restricciones/preview', methods=['POST'])
@login_required
def preview_restriction():
    data = request.json
    worker_id = data.get('trabajador_id')
    
    # Validar acceso al trabajador
    worker = db.get_or_404(Trabajador, worker_id)
    if not usuario_tiene_acceso(current_user, worker.empresa_id):
        return jsonify({'status': 'error', 'msg': 'Sin acceso a este trabajador'}), 403
    data = request.json
    worker_id = data.get('trabajador_id')
    fecha_inicio = datetime.strptime(data.get('fecha_inicio'), '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(data.get('fecha_fin'), '%Y-%m-%d').date()
    
    # Buscar solapamientos
    existentes = TrabajadorAusencia.query.filter(
        TrabajadorAusencia.trabajador_id == worker_id,
        TrabajadorAusencia.fecha_inicio <= fecha_fin,
        TrabajadorAusencia.fecha_fin >= fecha_inicio
    ).all()

    conflictos = []
    overwrites = 0
    respects = 0
    
    nueva_cat = data.get('categoria')
    tipo_id_raw = data.get('tipo_ausencia_id')
    
    if not nueva_cat and tipo_id_raw:
        if isinstance(tipo_id_raw, str) and tipo_id_raw.startswith('plantilla_'):
            from app.models.business import TipoAusenciaPlantilla
            p_id = int(tipo_id_raw.split('_')[1])
            p_obj = db.session.get(TipoAusenciaPlantilla, p_id)
            if p_obj: nueva_cat = p_obj.categoria
        else:
            tipo_m = db.session.get(TipoAusencia, tipo_id_raw)
            if tipo_m: nueva_cat = tipo_m.categoria

    for s in existentes:
        s_cat = s.tipo_ausencia.categoria if s.tipo_ausencia else CategoriaAusencia.AUSENCIA
        if nueva_cat == CategoriaAusencia.RESTRICCION and s_cat == CategoriaAusencia.AUSENCIA:
            respects += 1
            conflictos.append(f"Respetar: {s.tipo_ausencia.nombre} ({s.fecha_inicio} al {s.fecha_fin})")
        else:
            overwrites += 1
            conflictos.append(f"Reemplazar: {s.tipo_ausencia.nombre} ({s.fecha_inicio} al {s.fecha_fin})")

    msg = ""
    if respects > 0 and overwrites > 0:
        msg = f"Se detectaron {len(existentes)} solapamientos. Se respetarán {respects} ausencias y se reemplazarán {overwrites} restricciones."
    elif respects > 0:
        msg = f"Se detectaron {respects} ausencias en este rango. La nueva restricción se aplicará solo en los días libres restantes."
    elif overwrites > 0:
        msg = f"Se detectaron {overwrites} registros que serán reemplazados."

    return jsonify({
        'status': 'conflict' if conflictos else 'ok',
        'msg': msg,
        'conflictos': conflictos,
        'overwrite_warning': True if overwrites > 0 else False
    })

@restricciones_bp.route('/api/restricciones/save', methods=['POST'])
@login_required
def save_restriction():
    data = request.json
    worker_id = data.get('trabajador_id')

    # Validar acceso al trabajador
    worker = db.get_or_404(Trabajador, worker_id)
    if not usuario_tiene_acceso(current_user, worker.empresa_id):
        return jsonify({'status': 'error', 'msg': 'Sin acceso a este trabajador'}), 403
    data = request.json
    worker_id = data.get('trabajador_id')
    tipo_id_raw = data.get('tipo_ausencia_id')
    
    if isinstance(tipo_id_raw, str) and tipo_id_raw.startswith('plantilla_'):
        # Es una restricción universal/universo (pueden ser Días o Turnos)
        from app.models.business import TipoAusenciaPlantilla
        plantilla_id = int(tipo_id_raw.split('_')[1])
        p_obj = db.get_or_404(TipoAusenciaPlantilla, plantilla_id)
        
        # Buscar el equivalente en la empresa del trabajador
        if p_obj.categoria == CategoriaAusencia.RESTRICCION:
            # Mapeo por tipo_restriccion técnica
            tipo_maestro = TipoAusencia.query.filter_by(
                empresa_id=worker.empresa_id,
                tipo_restriccion=p_obj.tipo_restriccion
            ).first()
        else:
            # Mapeo por abreviación (para Vacaciones, Licencias, etc.)
            tipo_maestro = TipoAusencia.query.filter_by(
                empresa_id=worker.empresa_id,
                abreviacion=p_obj.abreviacion
            ).first()
        
        if not tipo_maestro:
            return jsonify({'status': 'error', 'msg': f'La empresa no tiene configurado el tipo {p_obj.nombre}.'}), 400
    else:
        tipo_maestro = db.get_or_404(TipoAusencia, tipo_id_raw)
    
    fecha_inicio = datetime.strptime(data.get('fecha_inicio'), '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(data.get('fecha_fin'), '%Y-%m-%d').date()
    
    # VALIDACIÓN DOMINGOS: No permitir TURNO_FIJO en domingos (dia 6)
    dias_semana = data.get('dias_semana', [])
    if tipo_maestro.categoria == CategoriaAusencia.RESTRICCION:
        rt_tipo = tipo_maestro.tipo_restriccion or RestrictionType.TURNO_FIJO
        if rt_tipo == RestrictionType.TURNO_FIJO and 6 in dias_semana:
            return jsonify({
                'status': 'error', 
                'msg': 'No se permite asignar turnos fijos los domingos por normativa de descanso legal obligatorio.'
            }), 400
    nueva_cat = tipo_maestro.categoria
    is_fixed = (nueva_cat == CategoriaAusencia.RESTRICCION and 
                (tipo_maestro.tipo_restriccion or RestrictionType.TURNO_FIJO) == RestrictionType.TURNO_FIJO)

    try:
        from app.services.legal_engine import LegalEngine
        trabajador_obj = db.session.get(Trabajador, worker_id)
        
        # VALIDACIÓN CARGA SEMANAL DINÁMICA: Sumar horas reales de los turnos seleccionados
        if is_fixed and trabajador_obj:
            horas_seleccionadas = 0
            if data.get('matrix'):
                # matrix es un dict { dia: shift_id }
                for d_idx, s_id in data['matrix'].items():
                    t_db = db.session.get(Turno, s_id)
                    if t_db: horas_seleccionadas += t_db.duracion_hrs
            
            max_h = LegalEngine.max_horas_semana(trabajador_obj)
            permite_extra = getattr(trabajador_obj, 'permite_horas_extra', False)
            
            if horas_seleccionadas > max_h and not permite_extra:
                return jsonify({
                    'status': 'error',
                    'msg': f'La carga horaria seleccionada ({horas_seleccionadas}h) excede el límite legal de su contrato ({max_h}h).'
                }), 400

        from datetime import timedelta
        
        # 1. SMART SPLIT: Buscar solapamientos y gestionar prioridades
        solapados = TrabajadorAusencia.query.filter(
            TrabajadorAusencia.trabajador_id == worker_id,
            TrabajadorAusencia.fecha_inicio <= fecha_fin,
            TrabajadorAusencia.fecha_fin >= fecha_inicio
        ).all()
        
        rangos_para_lo_nuevo = [(fecha_inicio, fecha_fin)]
        fragmentos_viejos = []
        a_eliminar = []

        for s in solapados:
            s_cat = s.tipo_ausencia.categoria if s.tipo_ausencia else CategoriaAusencia.AUSENCIA
            
            # REGLA DE PRIORIDAD: Si lo nuevo es RESTRICCION y lo viejo es AUSENCIA -> RESPETAR VIEJO
            if nueva_cat == CategoriaAusencia.RESTRICCION and s_cat == CategoriaAusencia.AUSENCIA:
                # Restamos el rango del viejo de lo que queremos cubrir con lo nuevo
                nuevos_rangos = []
                for b_start, b_end in rangos_para_lo_nuevo:
                    if s.fecha_inicio <= b_end and s.fecha_fin >= b_start:
                        if s.fecha_inicio > b_start:
                            nuevos_rangos.append((b_start, s.fecha_inicio - timedelta(days=1)))
                        if s.fecha_fin < b_end:
                            nuevos_rangos.append((s.fecha_fin + timedelta(days=1), b_end))
                    else:
                        nuevos_rangos.append((b_start, b_end))
                rangos_para_lo_nuevo = nuevos_rangos
                continue # Mantenemos el registro viejo intacto
            
            # En cualquier otro caso (Nuevo es AUSENCIA, o Nuevo es RESTRICCION sobre vieja RESTRICCION)
            # El nuevo manda -> Borramos el viejo y fragmentamos lo que sobresalga
            a_eliminar.append(s)
            
            # Detalles para recrear fragmentos del viejo si sobresale
            s_motivo = s.motivo
            s_tipo_id = s.tipo_ausencia_id
            rt_data = None
            if s.restriccion:
                rt = s.restriccion
                rt_data = {
                    'empresa_id': rt.empresa_id,
                    'tipo': rt.tipo,
                    'naturaleza': rt.naturaleza,
                    'dias_semana': rt.dias_semana,
                    'turno_id': rt.turno_id
                }

            # Fragmento ANTES
            if s.fecha_inicio < fecha_inicio:
                fragmentos_viejos.append({
                    'start': s.fecha_inicio,
                    'end': fecha_inicio - timedelta(days=1),
                    'tipo_id': s_tipo_id,
                    'motivo': s_motivo,
                    'rt_data': rt_data
                })
            
            # Fragmento DESPUES
            if s.fecha_fin > fecha_fin:
                fragmentos_viejos.append({
                    'start': fecha_fin + timedelta(days=1),
                    'end': s.fecha_fin,
                    'tipo_id': s_tipo_id,
                    'motivo': s_motivo,
                    'rt_data': rt_data
                })

        # 2. EJECUTAR LIMPIEZA
        for s in a_eliminar:
            if s.restriccion:
                db.session.delete(s.restriccion)
            db.session.delete(s)
        db.session.flush()

        # 3. CREAR FRAGMENTOS DE REGISTROS VIEJOS QUE SOBRESALIAN
        for frag in fragmentos_viejos:
            frag_rt_id = None
            if frag['rt_data']:
                d = frag['rt_data']
                nueva_rt = TrabajadorRestriccionTurno(
                    trabajador_id=worker_id,
                    empresa_id=d['empresa_id'],
                    tipo=d['tipo'],
                    naturaleza=d['naturaleza'],
                    fecha_inicio=frag['start'],
                    fecha_fin=frag['end'],
                    dias_semana=d['dias_semana'],
                    turno_id=d['turno_id'],
                    motivo=frag['motivo']
                )
                db.session.add(nueva_rt)
                db.session.flush()
                frag_rt_id = nueva_rt.id
            
            nueva_a = TrabajadorAusencia(
                trabajador_id=worker_id,
                tipo_ausencia_id=frag['tipo_id'],
                fecha_inicio=frag['start'],
                fecha_fin=frag['end'],
                motivo=frag['motivo'],
                restriccion_id=frag_rt_id
            )
            db.session.add(nueva_a)

        # 4. CREAR EL REGISTRO NUEVO (O FRAGMENTOS DEL MISMO)
        # SGT 2.1: Si es TURNO_FIJO, segmentamos para excluir domingos físicamente del rango
        final_segments = []

        if is_fixed:
            for r_start, r_end in rangos_para_lo_nuevo:
                curr_start = r_start
                curr = r_start
                while curr <= r_end:
                    if curr.weekday() == 6: # Es domingo
                        if curr > curr_start:
                            final_segments.append((curr_start, curr - timedelta(days=1)))
                        curr_start = curr + timedelta(days=1)
                    curr += timedelta(days=1)
                if curr_start <= r_end:
                    final_segments.append((curr_start, r_end))
        else:
            final_segments = rangos_para_lo_nuevo

        last_id = None
        for start, end in final_segments:
            restriccion_id = None
            if nueva_cat == CategoriaAusencia.RESTRICCION:
                rt_tipo = tipo_maestro.tipo_restriccion or RestrictionType.TURNO_FIJO
                rt_naturaleza = NATURALEZA_POR_TIPO.get(rt_tipo, 'hard')
                
                nueva_rt = TrabajadorRestriccionTurno(
                    trabajador_id=worker_id,
                    empresa_id=data.get('empresa_id'),
                    tipo=rt_tipo.value if hasattr(rt_tipo, 'value') else rt_tipo,
                    naturaleza=rt_naturaleza,
                    fecha_inicio=start,
                    fecha_fin=end,
                    dias_semana=data.get('dias_semana'),
                    turno_id=data.get('turno_id'),
                    motivo=data.get('motivo')
                )
                db.session.add(nueva_rt)
                db.session.flush()
                restriccion_id = nueva_rt.id

            nueva_ausencia = TrabajadorAusencia(
                trabajador_id=worker_id,
                tipo_ausencia_id=tipo_maestro.id,
                fecha_inicio=start,
                fecha_fin=end,
                motivo=data.get('motivo'),
                restriccion_id=restriccion_id
            )
            db.session.add(nueva_ausencia)
            db.session.flush()
            last_id = nueva_ausencia.id

        db.session.commit()
        return jsonify({'status': 'ok', 'id': last_id})
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@restricciones_bp.route('/api/restricciones/delete/<int:id>', methods=['POST'])
@login_required
def delete_restriction(id):
    # Aquí el ID es el de TrabajadorAusencia (el registro unificado)
    a = db.get_or_404(TrabajadorAusencia, id)
    
    # Validar acceso al trabajador dueño de la ausencia
    if not usuario_tiene_acceso(current_user, a.trabajador.empresa_id):
        return jsonify({'status': 'error', 'msg': 'Sin acceso a este registro'}), 403
    
    if a.restriccion:
        db.session.delete(a.restriccion)
    
    db.session.delete(a)
    db.session.commit()
    
    return jsonify({'status': 'ok'})

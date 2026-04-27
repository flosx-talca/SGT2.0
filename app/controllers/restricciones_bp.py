from flask import Blueprint, request, jsonify
from app.database import db
from app.models.business import Trabajador, TrabajadorRestriccionTurno, Turno
from app.models.enums import RestrictionType, NATURALEZA_POR_TIPO
from datetime import datetime

restricciones_bp = Blueprint('restricciones', __name__)

@restricciones_bp.route('/api/restricciones/worker/<int:worker_id>', methods=['GET'])
def get_worker_restrictions(worker_id):
    restricciones = TrabajadorRestriccionTurno.query.filter_by(trabajador_id=worker_id, activo=True).all()
    return jsonify([{
        'id': r.id,
        'tipo': r.tipo,
        'fecha_inicio': r.fecha_inicio.isoformat(),
        'fecha_fin': r.fecha_fin.isoformat(),
        'dias_semana': r.dias_semana,
        'turno': r.turno.nombre if r.turno else None,
        'motivo': r.motivo
    } for r in restricciones])

@restricciones_bp.route('/api/restricciones/preview', methods=['POST'])
def preview_restriction():
    data = request.json
    worker_id = data.get('trabajador_id')
    tipo = data.get('tipo')
    fecha_inicio = datetime.strptime(data.get('fecha_inicio'), '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(data.get('fecha_fin'), '%Y-%m-%d').date()
    dias_semana = data.get('dias_semana', []) # [0, 1, 2...]
    turno_id = data.get('turno_id')

    # Buscar conflictos
    conflictos = []
    
    # Restricciones existentes del trabajador en el rango de fechas
    existentes = TrabajadorRestriccionTurno.query.filter(
        TrabajadorRestriccionTurno.trabajador_id == worker_id,
        TrabajadorRestriccionTurno.activo == True,
        TrabajadorRestriccionTurno.fecha_inicio <= fecha_fin,
        TrabajadorRestriccionTurno.fecha_fin >= fecha_inicio
    ).all()

    for r in existentes:
        # Verificar solapamiento de días de la semana
        overlap_dias = set(dias_semana) & set(r.dias_semana or range(7))
        if not overlap_dias:
            continue

        # Lógica de conflicto
        if tipo == RestrictionType.TURNO_FIJO and r.tipo == RestrictionType.TURNO_FIJO:
            if r.turno_id != turno_id:
                conflictos.append(f"Ya existe un turno fijo ({r.turno.nombre}) en días solapados.")
        
        elif tipo == RestrictionType.EXCLUIR_TURNO and r.tipo == RestrictionType.TURNO_FIJO:
            if r.turno_id == turno_id:
                conflictos.append(f"No puedes excluir un turno que ya está marcado como FIJO.")

        elif tipo == RestrictionType.SOLO_TURNO and r.tipo == RestrictionType.SOLO_TURNO:
            conflictos.append("Ya existe una restricción de SOLO TURNO en este período.")

    return jsonify({
        'status': 'conflict' if conflictos else 'ok',
        'conflictos': conflictos
    })

@restricciones_bp.route('/api/restricciones/save', methods=['POST'])
def save_restriction():
    data = request.json
    tipo = data.get('tipo')
    
    nueva = TrabajadorRestriccionTurno(
        trabajador_id=data.get('trabajador_id'),
        empresa_id=data.get('empresa_id'),
        tipo=tipo,
        naturaleza=NATURALEZA_POR_TIPO.get(tipo, 'hard'),
        fecha_inicio=datetime.strptime(data.get('fecha_inicio'), '%Y-%m-%d').date(),
        fecha_fin=datetime.strptime(data.get('fecha_fin'), '%Y-%m-%d').date(),
        dias_semana=data.get('dias_semana'),
        turno_id=data.get('turno_id'),
        motivo=data.get('motivo')
    )
    
    db.session.add(nueva)
    db.session.commit()
    
    return jsonify({'status': 'ok', 'id': nueva.id})

@restricciones_bp.route('/api/restricciones/delete/<int:id>', methods=['POST'])
def delete_restriction(id):
    r = TrabajadorRestriccionTurno.query.get_or_404(id)
    r.activo = False
    db.session.commit()
    return jsonify({'status': 'ok'})

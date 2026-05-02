from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import select, desc
from app import db
from app.models.scheduling import CuadranteCabecera, CuadranteAsignacion
from app.services.cuadrante_service import guardar_cuadrante, editar_asignacion_manual

cuadrante_bp = Blueprint('cuadrante', __name__, url_prefix='/cuadrante')

@cuadrante_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    """Guarda el cuadrante generado por el Solver."""
    data = request.get_json()
    cabecera = guardar_cuadrante(
        empresa_id=data['empresa_id'],
        servicio_id=data.get('servicio_id'),
        mes=data['mes'],
        anio=data['anio'],
        asignaciones=data['asignaciones']
    )
    return jsonify({"ok": True, "cabecera_id": cabecera.id})


@cuadrante_bp.route('/asignacion', methods=['PUT'])
@login_required
def editar_asignacion():
    """Modifica una asignación manualmente post-guardado."""
    data   = request.get_json()
    ip     = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    try:
        asig = editar_asignacion_manual(
            cabecera_id=data.get('cabecera_id'),
            trabajador_id=data.get('trabajador_id'),
            fecha=data.get('fecha'),
            turno_nuevo_id=data.get('turno_id'),
            es_libre=data.get('es_libre', False),
            motivo=data.get('motivo', 'Cambio manual UI'),
            ip=ip
        )
        return jsonify({
            "ok": True,
            "asignacion_id": asig.id,
            "origen": asig.origen
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


@cuadrante_bp.route('/lista', methods=['GET'])
@login_required
def lista():
    """Retorna las últimas planificaciones para el DataTable del dashboard."""
    cabeceras = db.session.execute(
        select(CuadranteCabecera)
        .order_by(desc(CuadranteCabecera.guardado_en))
        .limit(50)
    ).scalars().all()

    # En HTMX, si la petición viene del dashboard, renderizar solo el partial
    is_htmx = request.headers.get('HX-Request', False)

    return render_template(
        'cuadrante/lista_partial.html',
        cabeceras=cabeceras,
        is_htmx=is_htmx
    )

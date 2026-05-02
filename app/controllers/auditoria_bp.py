from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.scheduling import CuadranteAuditoria, CuadranteCabecera
from app.services.context import get_empresas_usuario, get_empresa_activa_id
from flask_login import login_required, current_user

auditoria_bp = Blueprint('auditoria', __name__, url_prefix='/auditoria')

def get_auditoria_query():
    """Función auxiliar para obtener la query base filtrada."""
    # 1. Obtener empresas permitidas
    empresas_permitidas = get_empresas_usuario()
    permitidas_ids = [e.id for e in empresas_permitidas]
    
    # 2. Obtener empresa activa (filtro del menú lateral)
    activa_id = get_empresa_activa_id()
    
    query = CuadranteAuditoria.query.join(CuadranteCabecera)
    
    if activa_id:
        # Si hay una activa, filtramos por esa (siempre que esté entre las permitidas)
        if int(activa_id) in permitidas_ids:
            query = query.filter(CuadranteCabecera.empresa_id == activa_id)
        else:
            # Si intenta ver una empresa no permitida, no mostramos nada
            query = query.filter(CuadranteCabecera.empresa_id == -1)
    else:
        # Si no hay activa (Super Admin viendo todo), filtramos por todas las permitidas
        query = query.filter(CuadranteCabecera.empresa_id.in_(permitidas_ids))
        
    return query.order_by(CuadranteAuditoria.fecha_cambio.desc())

@auditoria_bp.route('/')
@login_required
def index():
    """Vista principal del historial de auditoría."""
    registros = get_auditoria_query().limit(200).all()
    return render_template('auditoria/index.html', registros=registros)

@auditoria_bp.route('/tabla')
@login_required
def tabla():
    """Partial para recarga de tabla de auditoría."""
    registros = get_auditoria_query().limit(200).all()
    return render_template('auditoria/partials/auditoria_rows.html', registros=registros)

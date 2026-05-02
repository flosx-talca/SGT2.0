from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.auth import Rol, Menu, RolMenu
from flask_login import login_required, current_user

permisos_bp = Blueprint('permisos', __name__, url_prefix='/permisos')

@permisos_bp.route('/')
@login_required
def index():
    """Vista principal de permisos (Solo Super Admin)."""
    if not current_user.is_super_admin:
        from flask import abort
        abort(403)
    
    roles = Rol.query.order_by(Rol.descripcion).all()
    return render_template('permisos/index.html', roles=roles)

@permisos_bp.route('/tabla')
@login_required
def tabla():
    """Partial para recargar la lista de roles."""
    if not current_user.is_super_admin:
        from flask import abort
        abort(403)
    
    roles = Rol.query.order_by(Rol.descripcion).all()
    return render_template('permisos/partials/rol_rows.html', roles=roles)

@permisos_bp.route('/modal', methods=['POST'])
@login_required
def modal():
    """Modal para gestionar los menús de un rol específico."""
    if not current_user.is_super_admin:
        from flask import abort
        abort(403)

    rol_id = request.form.get('id')
    rol = Rol.query.get_or_404(rol_id)
    
    # Obtener todos los menús activos
    todos_los_menus = Menu.query.filter_by(activo=True).order_by(Menu.orden).all()
    
    # Obtener los permisos actuales del rol
    permisos_actuales = {p.menu_id: p for p in rol.menus}
    
    return render_template('permisos/modal.html', 
                           rol=rol, 
                           menus=todos_los_menus, 
                           permisos=permisos_actuales)

@permisos_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    """Guarda la configuración de permisos para un rol."""
    if not current_user.is_super_admin:
        return jsonify({'ok': False, 'msg': 'No tiene permisos.'}), 403

    rol_id = request.form.get('rol_id')
    rol = Rol.query.get_or_404(rol_id)
    
    try:
        # 1. Eliminar permisos anteriores
        RolMenu.query.filter_by(rol_id=rol.id).delete()
        
        # 2. Procesar los nuevos menús seleccionados
        # El form enviará 'menu_ids[]' con los IDs de los menús marcados
        menu_ids = request.form.getlist('menu_ids[]')
        
        for m_id in menu_ids:
            # Capturar los permisos específicos (crear, editar, eliminar)
            # Estos vienen como 'p_crear_ID', 'p_editar_ID', etc.
            p_crear = request.form.get(f'p_crear_{m_id}') == 'on'
            p_editar = request.form.get(f'p_editar_{m_id}') == 'on'
            p_eliminar = request.form.get(f'p_eliminar_{m_id}') == 'on'
            
            nuevo_permiso = RolMenu(
                rol_id=rol.id,
                menu_id=int(m_id),
                puede_crear=p_crear,
                puede_editar=p_editar,
                puede_eliminar=p_eliminar
            )
            db.session.add(nuevo_permiso)
            
        db.session.commit()
        return jsonify({'ok': True, 'msg': f'Permisos para "{rol.descripcion}" actualizados correctamente.'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

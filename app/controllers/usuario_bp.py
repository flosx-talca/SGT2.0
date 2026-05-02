from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.auth import Usuario, Rol, UsuarioEmpresa
from app.models.business import Cliente, Empresa
from app.services.context import get_empresas_usuario
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuarios')

@usuario_bp.route('/')
@login_required
def index():
    if current_user.is_super_admin:
        registros = Usuario.query.order_by(Usuario.nombre).all()
    elif current_user.is_cliente:
        registros = Usuario.query.filter_by(cliente_id=current_user.cliente_id).order_by(Usuario.nombre).all()
    else:
        empresas = get_empresas_usuario()
        ids = [e.id for e in empresas]
        u_ids = [ue.usuario_id for ue in UsuarioEmpresa.query.filter(UsuarioEmpresa.empresa_id.in_(ids)).all()]
        registros = Usuario.query.filter(Usuario.id.in_(u_ids)).order_by(Usuario.nombre).all()
        
    return render_template('usuarios.html', registros=registros)

@usuario_bp.route('/tabla')
@login_required
def tabla():
    if current_user.is_super_admin:
        registros = Usuario.query.order_by(Usuario.nombre).all()
    elif current_user.is_cliente:
        registros = Usuario.query.filter_by(cliente_id=current_user.cliente_id).order_by(Usuario.nombre).all()
    else:
        empresas = get_empresas_usuario()
        ids = [e.id for e in empresas]
        u_ids = [ue.usuario_id for ue in UsuarioEmpresa.query.filter(UsuarioEmpresa.empresa_id.in_(ids)).all()]
        registros = Usuario.query.filter(Usuario.id.in_(u_ids)).order_by(Usuario.nombre).all()
        
    return render_template('partials/usuario_rows.html', registros=registros)

@usuario_bp.route('/modal', methods=['POST'])
@login_required
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Usuario.query.get_or_404(int(registro_id))
    
    # Filtrar roles permitidos
    query_roles = Rol.query.filter_by(activo=True)
    if not current_user.is_super_admin:
        # Clientes no pueden crear Super Admins ni otros Clientes (generalmente)
        query_roles = query_roles.filter(Rol.descripcion.notin_(['Super Admin', 'Cliente']))
    roles = query_roles.order_by(Rol.descripcion).all()
    
    # Filtrar clientes permitidos
    clientes = []
    if current_user.is_super_admin:
        clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all()
    
    return render_template('modal-usuario.html', 
                           modo=modo, 
                           registro=registro, 
                           roles=roles, 
                           clientes=clientes)

@usuario_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    uid = request.form.get('id', '').strip()
    rut = request.form.get('rut', '').strip()
    nombre = request.form.get('nombre', '').strip()
    apellidos = request.form.get('apellidos', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    rol_id = request.form.get('rol_id', '').strip()
    cliente_id = request.form.get('cliente_id', '').strip()
    activo = request.form.get('activo') == 'true'

    if not rut or not nombre or not email or not rol_id:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    try:
        # Si es cliente, forzamos su propio ID de cliente
        if current_user.is_cliente:
            cid = current_user.cliente_id
        else:
            cid = int(cliente_id) if cliente_id else None

        if uid and uid != '0':
            usuario = Usuario.query.get_or_404(int(uid))
            
            # Seguridad: un cliente solo puede editar sus usuarios
            if current_user.is_cliente and usuario.cliente_id != current_user.cliente_id:
                return jsonify({'ok': False, 'msg': 'No tiene permisos para editar este usuario.'}), 403

            usuario.rut = rut
            usuario.nombre = nombre
            usuario.apellidos = apellidos
            usuario.email = email
            usuario.rol_id = int(rol_id)
            usuario.cliente_id = cid
            usuario.activo = activo
            
            if password:
                usuario.password_hash = generate_password_hash(password)
            msg = f'Usuario "{nombre}" actualizado.'
        else:
            if not password:
                return jsonify({'ok': False, 'msg': 'La contraseña es obligatoria.'}), 400
            
            usuario = Usuario(
                rut=rut, nombre=nombre, apellidos=apellidos,
                email=email, password_hash=generate_password_hash(password),
                rol_id=int(rol_id), cliente_id=cid, activo=activo
            )
            db.session.add(usuario)
            msg = f'Usuario "{nombre}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

# --- GESTION DE EMPRESAS POR USUARIO ---

@usuario_bp.route('/empresas/modal', methods=['POST'])
@login_required
def modal_empresas():
    uid = request.form.get('id')
    usuario = Usuario.query.get_or_404(int(uid))
    
    # Obtener todas las empresas que el administrador (quien opera) puede ver
    empresas_visibles = get_empresas_usuario()
    
    # Obtener IDs de las empresas que el usuario (el objetivo) ya tiene asignadas
    ids_asignadas = [ue.empresa_id for ue in usuario.empresas if ue.activo]
    
    return render_template('modal-usuario-empresas.html', 
                           usuario=usuario, 
                           empresas=empresas_visibles, 
                           ids_asignadas=ids_asignadas)

@usuario_bp.route('/empresas/guardar', methods=['POST'])
@login_required
def guardar_empresas():
    uid = request.form.get('usuario_id')
    usuario = Usuario.query.get_or_404(int(uid))
    
    empresa_ids = request.form.getlist('empresa_ids[]')
    
    try:
        # Desactivar todas las asignaciones actuales primero
        UsuarioEmpresa.query.filter_by(usuario_id=usuario.id).delete()
        
        for eid in empresa_ids:
            nueva_rel = UsuarioEmpresa(
                usuario_id=usuario.id,
                empresa_id=int(eid),
                activo=True
            )
            db.session.add(nueva_rel)
            
        db.session.commit()
        return jsonify({'ok': True, 'msg': f'Accesos de "{usuario.nombre}" actualizados.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@usuario_bp.route('/eliminar', methods=['POST'])
@login_required
def eliminar():
    uid = request.form.get('id', '').strip()
    usuario = Usuario.query.get_or_404(int(uid))
    usuario.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Usuario desactivado.'})

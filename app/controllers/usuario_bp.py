from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.auth import Usuario, Rol
from app.models.business import Cliente
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
        # Administradores solo ven usuarios de sus empresas asignadas
        from app.services.context import get_empresas_usuario
        empresas = get_empresas_usuario()
        ids = [e.id for e in empresas]
        from app.models.auth import UsuarioEmpresa
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
        from app.services.context import get_empresas_usuario
        empresas = get_empresas_usuario()
        ids = [e.id for e in empresas]
        from app.models.auth import UsuarioEmpresa
        u_ids = [ue.usuario_id for ue in UsuarioEmpresa.query.filter(UsuarioEmpresa.empresa_id.in_(ids)).all()]
        registros = Usuario.query.filter(Usuario.id.in_(u_ids)).order_by(Usuario.nombre).all()
        
    return render_template('partials/usuario_rows.html', registros=registros)

@usuario_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Usuario.query.get_or_404(int(registro_id))
    
    roles = Rol.query.filter_by(activo=True).order_by(Rol.descripcion).all()
    clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all()
    
    return render_template('modal-usuario.html', 
                           modo=modo, 
                           registro=registro, 
                           roles=roles, 
                           clientes=clientes)

@usuario_bp.route('/guardar', methods=['POST'])
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
        cid = int(cliente_id) if cliente_id else None

        if uid and uid != '0':
            usuario = Usuario.query.get_or_404(int(uid))
            # Validar duplicados
            dup_rut = Usuario.query.filter(Usuario.rut == rut, Usuario.id != usuario.id).first()
            if dup_rut: return jsonify({'ok': False, 'msg': 'El RUT ya está registrado.'}), 409
            
            dup_email = Usuario.query.filter(Usuario.email == email, Usuario.id != usuario.id).first()
            if dup_email: return jsonify({'ok': False, 'msg': 'El email ya está registrado.'}), 409

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
                return jsonify({'ok': False, 'msg': 'La contraseña es obligatoria para nuevos usuarios.'}), 400
            
            if Usuario.query.filter_by(rut=rut).first():
                return jsonify({'ok': False, 'msg': 'El RUT ya existe.'}), 409
            if Usuario.query.filter_by(email=email).first():
                return jsonify({'ok': False, 'msg': 'El email ya existe.'}), 409

            usuario = Usuario(
                rut=rut,
                nombre=nombre,
                apellidos=apellidos,
                email=email,
                password_hash=generate_password_hash(password),
                rol_id=int(rol_id),
                cliente_id=cid,
                activo=activo
            )
            db.session.add(usuario)
            msg = f'Usuario "{nombre}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@usuario_bp.route('/eliminar', methods=['POST'])
def eliminar():
    uid = request.form.get('id', '').strip()
    usuario = Usuario.query.get_or_404(int(uid))
    usuario.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Usuario desactivado.'})

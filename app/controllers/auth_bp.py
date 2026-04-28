from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.database import db
from app.models.auth import Usuario, UsuarioEmpresa
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        usuario_val = request.form.get('usuario', '').strip()
        password_val = request.form.get('password', '').strip()
        
        # Buscar por RUT, Email o alias 'admin'
        if usuario_val.lower() == 'admin':
            user = Usuario.query.filter_by(rut='99999999-9').first()
        else:
            # Normalizar RUT para búsqueda (quitar puntos y guiones si parece un RUT)
            import re
            rut_normalizado = re.sub(r'[^0-9kK]', '', usuario_val)
            
            user = Usuario.query.filter(
                (Usuario.rut == usuario_val) | 
                (Usuario.rut == rut_normalizado) | 
                (Usuario.email == usuario_val)
            ).first()
        
        if user and user.activo:
            print(f"DEBUG: Usuario encontrado: {user.rut}")
            # Soporte temporal para hashes SHA256 planos del dump inicial si fuera necesario
            is_valid = False
            try:
                is_valid = check_password_hash(user.password_hash, password_val)
                print(f"DEBUG: Password check_password_hash: {is_valid}")
            except Exception as e:
                print(f"DEBUG: Error check_password_hash: {e}")
                # Si falla, podría ser un hash plano
                import hashlib
                flat_hash = hashlib.sha256(password_val.encode()).hexdigest()
                if flat_hash == user.password_hash:
                    is_valid = True
                    print(f"DEBUG: Password flat_hash: {is_valid}")
                    # Actualizar a hash seguro de Werkzeug
                    user.password_hash = generate_password_hash(password_val)
                    db.session.commit()

            if is_valid:
                login_user(user)
                
                # SGT 2.1: Usar el servicio de contexto para obtener empresas accesibles
                from app.services.context import get_empresas_usuario
                empresas_disponibles = get_empresas_usuario()
                
                # Si solo tiene una empresa, activarla de una vez
                if len(empresas_disponibles) == 1:
                    user.empresa_activa_id = empresas_disponibles[0].id
                    db.session.commit()
                    return jsonify({'ok': True, 'msg': 'Bienvenido', 'redirect': url_for('main.index')})
                
                # Si tiene varias, debe elegir
                if len(empresas_disponibles) > 1:
                    return jsonify({'ok': True, 'msg': 'Seleccione empresa', 'redirect': url_for('auth.select_company')})
                
                # Super Admin sin empresas asignadas directamente (ve todo)
                if user.is_super_admin:
                    return jsonify({'ok': True, 'msg': 'Bienvenido Admin', 'redirect': url_for('main.index')})
                
                return jsonify({'ok': False, 'msg': 'Usuario sin empresas asignadas.'})
            else:
                return jsonify({'ok': False, 'msg': 'Credenciales inválidas.'})
        else:
            return jsonify({'ok': False, 'msg': 'Usuario no encontrado o inactivo.'})

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/select_company')
@login_required
def select_company():
    from app.services.context import get_empresas_usuario
    empresas_obj = get_empresas_usuario()
    if not empresas_obj and current_user.rol.descripcion != 'Super Admin':
        flash('No tienes empresas asignadas.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Adaptar para el template que espera objetos con propiedad .empresa
    # (Como venían de UsuarioEmpresa)
    class Adaptador:
        def __init__(self, e): self.empresa = e

    empresas = [Adaptador(e) for e in empresas_obj]
    return render_template('auth/select_company.html', empresas=empresas)

@auth_bp.route('/set_company/<int:empresa_id>')
@login_required
def set_company(empresa_id):
    # Verificar que el usuario tenga acceso a esa empresa
    from app.services.context import usuario_tiene_acceso
    if not usuario_tiene_acceso(current_user, empresa_id):
        flash('No tienes acceso a esta empresa.', 'danger')
        return redirect(url_for('auth.select_company'))
    
    current_user.empresa_activa_id = empresa_id
    from flask import session
    session['empresa_activa_id'] = empresa_id
    db.session.commit()
    return redirect(url_for('main.index'))

@auth_bp.route('/clear_company')
@login_required
def clear_company():
    if current_user.rol.descripcion != 'Super Admin':
        return redirect(url_for('auth.select_company'))
    
    current_user.empresa_activa_id = None
    from flask import session
    session.pop('empresa_activa_id', None)
    db.session.commit()
    return redirect(url_for('main.index'))

import sys, os
sys.path.append(os.getcwd())
from app import create_app
from app.models.auth import Usuario, Rol, UsuarioEmpresa
from app.models.business import Empresa, Trabajador
from app.database import db
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    cliente_rol = Rol.query.filter_by(descripcion='Cliente').first()
    emp_demo = Empresa.query.get(1)
    
    # Crear usuario Orlando si no existe
    orlando_user = Usuario.query.filter_by(rut='157742477').first()
    if not orlando_user:
        orlando_user = Usuario(
            rut='157742477',
            nombre='Orlando',
            apellidos='Usuario',
            email='orlando@sgt.cl',
            password_hash=generate_password_hash('1234'),
            rol_id=cliente_rol.id,
            activo=True
        )
        db.session.add(orlando_user)
        db.session.commit()
        print(f"Usuario Orlando creado.")
    else:
        orlando_user.rol_id = cliente_rol.id
        db.session.commit()
        print(f"Usuario Orlando actualizado a rol Cliente.")

    # Vincular a Empresa 1
    if emp_demo:
        ue = UsuarioEmpresa.query.filter_by(usuario_id=orlando_user.id, empresa_id=emp_demo.id).first()
        if not ue:
            ue = UsuarioEmpresa(usuario_id=orlando_user.id, empresa_id=emp_demo.id, activo=True)
            db.session.add(ue)
        orlando_user.empresa_activa_id = emp_demo.id
        db.session.commit()
        print(f"Orlando vinculado a {emp_demo.razon_social}.")

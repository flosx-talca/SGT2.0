
from app import create_app, db
from app.models.auth import Usuario, Rol, UsuarioEmpresa
from app.models.business import Empresa
from werkzeug.security import generate_password_hash
import random

def generate_rut():
    number = random.randint(10000000, 25000000)
    return f"{number}-{random.choice('0123456789K')}"

def add_users():
    app = create_app()
    with app.app_context():
        print("--- Agregando Usuarios Administradores a Empresas Demo ---")
        
        # Obtener el rol de Administrador
        rol_admin = Rol.query.filter_by(descripcion='Administrador').first()
        if not rol_admin:
            print("Error: No se encontró el rol de Administrador.")
            return

        # Obtener las 3 empresas más recientes (las que acabamos de crear)
        empresas = Empresa.query.order_by(Empresa.id.desc()).limit(3).all()
        
        for e in empresas:
            # Crear un usuario administrador para esta empresa
            email = f"admin@{e.razon_social.lower().split(' - ')[0].replace(' ', '')}.cl"
            
            # Verificar si ya existe
            user = Usuario.query.filter_by(email=email).first()
            if not user:
                user = Usuario(
                    rut=generate_rut(),
                    nombre="Admin",
                    apellidos=e.razon_social,
                    email=email,
                    password_hash=generate_password_hash('admin123'),
                    rol_id=rol_admin.id,
                    cliente_id=e.cliente_id,
                    empresa_activa_id=e.id
                )
                db.session.add(user)
                db.session.flush()
                
                # Vincular en usuario_empresa
                ue = UsuarioEmpresa(usuario_id=user.id, empresa_id=e.id)
                db.session.add(ue)
                print(f"Creado usuario: {email} / admin123 para Empresa: {e.razon_social}")
            else:
                print(f"Usuario {email} ya existe.")

        db.session.commit()
        print("--- Proceso Finalizado ---")

if __name__ == "__main__":
    add_users()

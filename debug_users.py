from app import create_app
from app.models.auth import Usuario

app = create_app()
with app.app_context():
    for u in Usuario.query.all():
        print(f"User: |{u.rut}|, Email: |{u.email}|, Rol: {u.rol.descripcion if u.rol else 'SIN ROL'}, Activo: {u.activo}, Empresas: {[ue.empresa_id for ue in u.empresas]}")

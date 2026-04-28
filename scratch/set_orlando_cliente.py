import sys, os
sys.path.append(os.getcwd())
from app import create_app
from app.models.auth import Usuario, Rol, UsuarioEmpresa
from app.models.business import Empresa
from app.database import db

app = create_app()
with app.app_context():
    # Buscar a Orlando
    orlando = Usuario.query.filter(Usuario.nombre.ilike('%Orlando%')).first()
    cliente_rol = Rol.query.filter_by(descripcion='Cliente').first()
    
    if orlando and cliente_rol:
        print(f"Encontrado: {orlando.nombre} {orlando.apellidos} (ID: {orlando.id})")
        orlando.rol_id = cliente_rol.id
        
        # Asegurar que tiene una empresa activa si tiene empresas vinculadas
        ue = UsuarioEmpresa.query.filter_by(usuario_id=orlando.id).first()
        if ue:
            orlando.empresa_activa_id = ue.empresa_id
            print(f"Empresa activa asignada: {ue.empresa_id}")
        
        db.session.commit()
        print(f"Rol 'Cliente' asignado exitosamente a {orlando.nombre}.")
    else:
        if not orlando:
            print("No se encontro al usuario Orlando.")
        if not cliente_rol:
            print("No se encontro el rol 'Cliente'.")

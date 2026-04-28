import sys, os
sys.path.append(os.getcwd())
from app import create_app
from app.models.auth import Usuario, UsuarioEmpresa
from app.models.business import Empresa
from app.database import db

app = create_app()
with app.app_context():
    orlando = Usuario.query.filter_by(rut='157742477').first()
    emp_orlando = Empresa.query.get(2)
    
    if orlando and emp_orlando:
        # Eliminar vinculos anteriores si es necesario (o solo agregar el nuevo)
        # El usuario pidio que este vinculado a ESTA empresa.
        
        ue = UsuarioEmpresa.query.filter_by(usuario_id=orlando.id, empresa_id=emp_orlando.id).first()
        if not ue:
            ue = UsuarioEmpresa(usuario_id=orlando.id, empresa_id=emp_orlando.id, activo=True)
            db.session.add(ue)
        
        orlando.empresa_activa_id = emp_orlando.id
        db.session.commit()
        print(f"Orlando vinculado exitosamente a {emp_orlando.razon_social}.")
    else:
        print("No se encontro a Orlando o la Empresa.")

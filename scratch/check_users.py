import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.getcwd())

from app import create_app
from app.models.auth import Usuario, Rol

app = create_app()
with app.app_context():
    roles = Rol.query.all()
    print("ROLES:")
    for r in roles:
        print(f"ID: {r.id} | Descripcion: {r.descripcion}")
    
    print("\nUSUARIOS:")
    usuarios = Usuario.query.all()
    for u in usuarios:
        print(f"ID: {u.id} | Rut: {u.rut} | Rol: {u.rol.descripcion if u.rol else 'None'}")

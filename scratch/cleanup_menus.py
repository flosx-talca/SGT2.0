import sys, os
sys.path.append(os.getcwd())
from app import create_app
from app.models.auth import Menu, RolMenu
from app.database import db

app = create_app()
with app.app_context():
    # Identificar duplicados por endpoint
    # Dejaremos el que NO tiene acento en el nombre (los nuevos que cree)
    
    menus = Menu.query.all()
    endpoints_vistos = {}
    
    for m in menus:
        if m.endpoint in endpoints_vistos:
            m_old = endpoints_vistos[m.endpoint]
            # Decidir cual borrar. Borraremos el que tenga caracteres extraños o sea el mas viejo.
            # Los nuevos IDs son > 22.
            
            # Si el actual es mas nuevo, borramos el viejo
            if m.id > m_old.id:
                to_delete = m_old
                endpoints_vistos[m.endpoint] = m
            else:
                to_delete = m
            
            print(f"Borrando duplicado: {to_delete.nombre} (ID: {to_delete.id}) para endpoint {to_delete.endpoint}")
            # Eliminar sus RolMenu primero
            RolMenu.query.filter_by(menu_id=to_delete.id).delete()
            db.session.delete(to_delete)
        else:
            endpoints_vistos[m.endpoint] = m
            
    db.session.commit()
    print("Limpieza de menus duplicados completada.")

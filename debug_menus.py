from app import create_app
from app.models.auth import Menu, Rol, RolMenu

app = create_app()
with app.app_context():
    print("--- MENUS EN BD ---")
    menus = Menu.query.all()
    for m in menus:
        print(f"ID: {m.id}, Nombre: {m.nombre}, Endpoint: {m.endpoint}, Icono: {m.icono}, Orden: {m.orden}")
    
    print("\n--- ROLES Y SUS MENUS ---")
    roles = Rol.query.all()
    for r in roles:
        print(f"Rol: {r.descripcion}")
        for rm in r.menus:
            print(f"  -> Menu: {rm.menu_asociado.nombre} (Activo: {rm.menu_asociado.activo})")

from app import create_app
from app.database import db
from app.models.auth import Menu, Rol, RolMenu, Usuario, UsuarioEmpresa
from app.models.business import Empresa

def setup_auth_data():
    app = create_app()
    with app.app_context():
        print("Configurando datos de menú y roles...")
        
        # 1. Actualizar Menús con endpoints e iconos
        menus_data = [
            # Operativos (Base)
            ('Dashboard', 'main.index', 'fa fa-th-large', 1, True),
            ('Trabajadores', 'trabajador.index', 'fa fa-users', 2, True),
            ('Turnos', 'turno.index', 'fa fa-clock', 3, True),
            ('Ausencias', 'ausencia.index', 'fa fa-calendar-times', 4, True),
            ('Tipos de Ausencia', 'tipo_ausencia.index', 'fa fa-user-minus', 5, True),
            ('Planificación', 'main.planificacion', 'fa fa-calendar-alt', 6, True),
            ('Simulación', 'main.simulacion', 'fa fa-robot', 7, True),
            
            # Administración (Globales)
            ('Clientes', 'cliente.index', 'fa fa-handshake', 20, False),
            ('Empresas', 'empresa.index', 'fa fa-building', 21, False),
            ('Servicios', 'servicio.index', 'fa fa-concierge-bell', 22, False),
            ('Usuarios', 'usuario.index', 'fa fa-users-cog', 23, False),
            ('Roles', 'rol.index', 'fa fa-id-badge', 24, False),
            ('Menús', 'menu.index', 'fa fa-list', 25, False),
            
            # Ubicación y Tiempo
            ('Regiones', 'region.index', 'fa fa-map-marked-alt', 30, False),
            ('Comunas', 'comuna.index', 'fa fa-map-pin', 31, False),
            ('Feriados', 'feriado.index', 'fa fa-umbrella-beach', 32, False),
            
            # Configuración Avanzada
            ('Reglas Empresa', 'regla_empresa.index', 'fa fa-briefcase', 40, False),
            ('Reglas Familia', 'main.reglas_familias', 'fa fa-layer-group', 41, False),
            ('Reglas Generales', 'regla.index', 'fa fa-cogs', 42, False),
            ('Configuración Reglas', 'main.reglas_config', 'fa fa-sliders-h', 43, False),
            ('Parámetros Legales', 'parametro_legal.index', 'fa fa-gavel', 44, False),
        ]
        
        for nombre, endpoint, icono, orden, es_base in menus_data:
            m = Menu.query.filter_by(nombre=nombre).first()
            if not m:
                m = Menu(nombre=nombre)
                db.session.add(m)
            
            m.endpoint = endpoint
            m.icono = icono
            m.orden = orden
            m.es_base = es_base
            m.activo = True
        
        db.session.commit()
        
        # 2. Asegurar que el Super Admin tenga acceso a todo
        admin_rol = Rol.query.filter_by(descripcion='Super Admin').first()
        if admin_rol:
            all_menus = Menu.query.all()
            for m in all_menus:
                exists = RolMenu.query.filter_by(rol_id=admin_rol.id, menu_id=m.id).first()
                if not exists:
                    rm = RolMenu(rol_id=admin_rol.id, menu_id=m.id, puede_crear=True, puede_editar=True, puede_eliminar=True)
                    db.session.add(rm)
        
        # 3. Asignar empresa 1 al usuario admin (para pruebas)
        admin_user = Usuario.query.filter_by(rut='99999999-9').first()
        emp_demo = Empresa.query.get(1)
        if admin_user and emp_demo:
            exists = UsuarioEmpresa.query.filter_by(usuario_id=admin_user.id, empresa_id=emp_demo.id).first()
            if not exists:
                ue = UsuarioEmpresa(usuario_id=admin_user.id, empresa_id=emp_demo.id, activo=True)
                db.session.add(ue)
            admin_user.empresa_activa_id = emp_demo.id

        db.session.commit()
        print("Configuracion completada.")

if __name__ == "__main__":
    setup_auth_data()

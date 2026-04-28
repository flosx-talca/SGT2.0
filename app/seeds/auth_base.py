from app.database import db
from app.models.auth import Menu, Rol, RolMenu, Usuario, UsuarioEmpresa
from app.models.business import Empresa
from werkzeug.security import generate_password_hash

def seed_auth_base():
    # Inicializa roles, menus y el usuario administrador base.
    print(" -> Configurando roles y menus base...")
    
    # 1. Definir Menus (Operativos y Administrativos)
    menus_data = [
        # Operativos (Base)
        ('Dashboard', 'main.index', 'fa fa-th-large', 1, True),
        ('Trabajadores', 'trabajador.index', 'fa fa-users', 2, True),
        ('Turnos', 'turno.index', 'fa fa-clock', 3, True),
        ('Ausencias', 'ausencia.index', 'fa fa-calendar-times', 4, True),
        ('Tipos de Ausencia', 'tipo_ausencia.index', 'fa fa-user-minus', 5, True),
        ('Planificacion', 'main.planificacion', 'fa fa-calendar-alt', 6, True),
        ('Simulacion', 'main.simulacion', 'fa fa-robot', 7, True),
        
        # Administracion (Globales)
        ('Clientes', 'cliente.index', 'fa fa-handshake', 20, False),
        ('Empresas', 'empresa.index', 'fa fa-building', 21, False),
        ('Servicios', 'servicio.index', 'fa fa-concierge-bell', 22, False),
        ('Usuarios', 'usuario.index', 'fa fa-users-cog', 23, False),
        ('Roles', 'rol.index', 'fa fa-id-badge', 24, False),
        ('Menus', 'menu.index', 'fa fa-list', 25, False),
        
        # Ubicacion y Tiempo
        ('Regiones', 'region.index', 'fa fa-map-marked-alt', 30, False),
        ('Comunas', 'comuna.index', 'fa fa-map-pin', 31, False),
        ('Feriados', 'feriado.index', 'fa fa-umbrella-beach', 32, False),
        
        # Configuracion Avanzada
        ('Reglas Empresa', 'regla_empresa.index', 'fa fa-briefcase', 40, False),
        ('Reglas Familia', 'main.reglas_familias', 'fa fa-layer-group', 41, False),
        ('Reglas Generales', 'regla.index', 'fa fa-cogs', 42, False),
        ('Configuracion Reglas', 'main.reglas_config', 'fa fa-sliders-h', 43, False),
        ('Parametros Legales', 'parametro_legal.index', 'fa fa-gavel', 44, False),
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
    
    # 2. Definir Roles (y limpiar antiguos)
    roles_data = ['Super Admin', 'Cliente', 'Administrador']
    for desc in roles_data:
        r = Rol.query.filter_by(descripcion=desc).first()
        if not r:
            r = Rol(descripcion=desc)
            db.session.add(r)
    
    # Eliminar roles que no esten en la lista (opcional, pero solicitado)
    old_roles = Rol.query.filter(~Rol.descripcion.in_(roles_data)).all()
    for orol in old_roles:
        # Nota: Esto podria fallar si hay usuarios asignados a estos roles
        try:
            # Primero eliminar sus RolMenu para evitar errores de FK
            RolMenu.query.filter_by(rol_id=orol.id).delete()
            db.session.delete(orol)
        except:
            print(f" (!) No se pudo eliminar el rol {orol.descripcion} (posiblemente tiene usuarios asignados)")
    
    db.session.commit()
    
    # 3. Asignar Menus a Roles
    admin_rol = Rol.query.filter_by(descripcion='Super Admin').first()
    cliente_rol = Rol.query.filter_by(descripcion='Cliente').first()
    admin_emp_rol = Rol.query.filter_by(descripcion='Administrador').first()
    
    all_menus = Menu.query.all()
    for m in all_menus:
        # Super Admin: Todo
        if admin_rol:
            if not RolMenu.query.filter_by(rol_id=admin_rol.id, menu_id=m.id).first():
                db.session.add(RolMenu(rol_id=admin_rol.id, menu_id=m.id, puede_crear=True, puede_editar=True, puede_eliminar=True))
        
        # Cliente y Administrador: Solo Base (Operativos)
        if m.es_base:
            if cliente_rol:
                if not RolMenu.query.filter_by(rol_id=cliente_rol.id, menu_id=m.id).first():
                    db.session.add(RolMenu(rol_id=cliente_rol.id, menu_id=m.id, puede_crear=True, puede_editar=True, puede_eliminar=True))
            if admin_emp_rol:
                if not RolMenu.query.filter_by(rol_id=admin_emp_rol.id, menu_id=m.id).first():
                    db.session.add(RolMenu(rol_id=admin_emp_rol.id, menu_id=m.id, puede_crear=True, puede_editar=True, puede_eliminar=True))
    
    db.session.commit()
    
    # 4. Usuario Admin por defecto
    admin_user = Usuario.query.filter_by(rut='99999999-9').first()
    if not admin_user:
        admin_user = Usuario(
            rut='99999999-9',
            nombre='Admin',
            apellidos='Sistema',
            email='admin@sgt.cl',
            password_hash=generate_password_hash('1234'),
            rol_id=admin_rol.id,
            activo=True
        )
        db.session.add(admin_user)
        db.session.commit()
    
    # 5. Empresa 1
    emp_demo = Empresa.query.get(1)
    if admin_user and emp_demo:
        ue = UsuarioEmpresa.query.filter_by(usuario_id=admin_user.id, empresa_id=emp_demo.id).first()
        if not ue:
            ue = UsuarioEmpresa(usuario_id=admin_user.id, empresa_id=emp_demo.id, activo=True)
            db.session.add(ue)
        admin_user.empresa_activa_id = emp_demo.id
        db.session.commit()

    print(" Base de autenticacion sembrada.")

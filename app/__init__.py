from flask import Flask, request as flask_request
from datetime import datetime
from .config import Config
from .database import db
from flask_migrate import Migrate
from flask_login import LoginManager
from . import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar plugins
    db.init_app(app)
    Migrate(app, db)

    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, inicie sesión para acceder a esta página."
    login_manager.login_message_category = "info"

    from .models.auth import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        from sqlalchemy.orm import joinedload
        # Usar joinedload para evitar "Parent instance is not bound to a Session" en el rol
        return Usuario.query.options(joinedload(Usuario.rol)).get(int(user_id))

    # DEBUG: Ver qué URL se está usando realmente
    print(f"\n--- DEBUG: SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')} ---\n")

    # Inyectar variables globales en todos los templates automáticamente
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.services.context import get_empresas_usuario, get_empresa_activa
        from app.models.auth import Menu, RolMenu

        context = {
            'is_htmx': flask_request.headers.get('HX-Request', False),
            'now': datetime.utcnow(),
            'nav_menus': [],
            'empresas_usuario': [],
            'empresa_activa': None
        }

        if current_user.is_authenticated:
            # Contexto multiempresa
            context['empresas_usuario'] = get_empresas_usuario()
            context['empresa_activa'] = get_empresa_activa()

            # Menus dinámicos
            rol_id_to_use = current_user.rol_id
            
            # Si es Super Admin y tiene una empresa seleccionada, 
            # mostramos el menú como Cliente para facilitar la gestión operativa.
            if current_user.is_super_admin and context['empresa_activa']:
                from app.models.auth import Rol
                cliente_rol = Rol.query.filter_by(descripcion='Cliente').first()
                if cliente_rol:
                    rol_id_to_use = cliente_rol.id

            context['nav_menus'] = Menu.query.join(RolMenu).filter(
                RolMenu.rol_id == rol_id_to_use,
                Menu.activo == True
            ).order_by(Menu.orden).all()

        return context


    from flask import redirect, url_for
    from flask_login import current_user

    @app.before_request
    def require_login():
        # Rutas públicas o estáticas
        if flask_request.endpoint in ['auth.login', 'static'] or not flask_request.endpoint:
            return
        
        print(f"DEBUG: Endpoint: {flask_request.endpoint}, User Authenticated: {current_user.is_authenticated}")
        
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Obligar a elegir empresa si no hay una activa
        # Excepto en las rutas de selección de empresa
        if not current_user.empresa_activa_id:
            if flask_request.endpoint not in ['auth.select_company', 'auth.set_company', 'auth.logout']:
                # Los Super Admin pueden navegar sin empresa si el controlador lo permite, 
                # pero para la mayoría de las vistas operativas, es mejor forzar la selección.
                if current_user.rol.descripcion != 'Super Admin':
                    return redirect(url_for('auth.select_company'))

    # Registrar Blueprints
    from .controllers.auth_bp import auth_bp
    from .controllers.main_bp import main_bp
    from .controllers.region_bp import region_bp
    from .controllers.comuna_bp import comuna_bp
    from .controllers.feriado_bp import feriado_bp
    from .controllers.servicio_bp import servicio_bp
    from .controllers.rol_bp import rol_bp
    from .controllers.menu_bp import menu_bp
    from .controllers.cliente_bp import cliente_bp
    from .controllers.empresa_bp import empresa_bp
    from .controllers.turno_bp import turno_bp
    from .controllers.usuario_bp import usuario_bp
    from .controllers.trabajador_bp import trabajador_bp
    from .controllers.regla_bp import regla_bp
    from .controllers.regla_empresa_bp import regla_empresa_bp
    from .controllers.planificacion_bp import planificacion_bp
    from .controllers.tipo_ausencia_bp import tipo_ausencia_bp
    from .controllers.ausencia_bp import ausencia_bp
    from .controllers.restricciones_bp import restricciones_bp
    from .controllers.parametro_legal_bp import parametro_legal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(region_bp)
    app.register_blueprint(comuna_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(servicio_bp)
    app.register_blueprint(trabajador_bp)
    app.register_blueprint(turno_bp)
    app.register_blueprint(planificacion_bp)
    app.register_blueprint(regla_bp)
    app.register_blueprint(regla_empresa_bp)
    app.register_blueprint(feriado_bp)
    app.register_blueprint(tipo_ausencia_bp)
    app.register_blueprint(ausencia_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(rol_bp)
    app.register_blueprint(restricciones_bp)
    app.register_blueprint(parametro_legal_bp)

    return app

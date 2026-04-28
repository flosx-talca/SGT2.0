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
        return Usuario.query.get(int(user_id))

    # DEBUG: Ver qué URL se está usando realmente
    print(f"\n--- DEBUG: SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')} ---\n")

    # Inyectar variables globales en todos los templates automáticamente
    @app.context_processor
    def inject_globals():
        return {
            'is_htmx': flask_request.headers.get('HX-Request', False),
            'now': datetime.utcnow()
        }

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

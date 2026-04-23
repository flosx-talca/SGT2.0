from flask import Flask, request as flask_request
from .config import Config
from .database import db
from . import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar plugins
    db.init_app(app)

    # Inyectar is_htmx en todos los templates automáticamente
    @app.context_processor
    def inject_htmx():
        return {'is_htmx': flask_request.headers.get('HX-Request', False)}

    # Registrar Blueprints
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

    app.register_blueprint(main_bp)
    app.register_blueprint(region_bp)
    app.register_blueprint(comuna_bp)
    app.register_blueprint(feriado_bp)
    app.register_blueprint(servicio_bp)
    app.register_blueprint(rol_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(turno_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(trabajador_bp)
    app.register_blueprint(regla_bp)
    app.register_blueprint(regla_empresa_bp)
    app.register_blueprint(planificacion_bp)

    return app

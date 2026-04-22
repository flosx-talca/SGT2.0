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
    app.register_blueprint(main_bp)
    app.register_blueprint(region_bp)
    app.register_blueprint(comuna_bp)

    return app

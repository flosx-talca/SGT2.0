from flask import Flask
from .config import Config
from .database import db
from . import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar plugins
    db.init_app(app)

    # Registrar Blueprints
    from .controllers.main_bp import main_bp
    from .controllers.region_bp import region_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(region_bp)

    return app

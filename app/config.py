import os
from dotenv import load_dotenv

# Forzamos la carga del .env y que sobrescriba variables globales
load_dotenv(override=True)

class Config:
    # Obtenemos la URL y la limpiamos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/sgt').split('?')[0]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "client_encoding": "utf8",
            "application_name": "SGT_App"
        }
    }
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

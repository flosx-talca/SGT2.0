import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app
from app.seeds.reglas_base import seed_reglas_base

app = create_app()
with app.app_context():
    seed_reglas_base()

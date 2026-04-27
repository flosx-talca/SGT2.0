import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

# Mock dotenv to avoid ModuleNotFoundError
import sys
from types import ModuleType
m = ModuleType("dotenv")
m.load_dotenv = lambda *args, **kwargs: None
sys.modules["dotenv"] = m

from app import create_app
from app.seeds.reglas_base import seed_reglas_base

app = create_app()
with app.app_context():
    seed_reglas_base()

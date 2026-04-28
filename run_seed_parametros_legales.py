import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

# Mock dotenv to avoid ModuleNotFoundError if not in environment
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    from types import ModuleType
    m = ModuleType("dotenv")
    m.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = m

from app import create_app
from app.seeds.parametros_legales import seed_parametros_legales

app = create_app()
with app.app_context():
    seed_parametros_legales()
    print("Legal parameters seeded successfully.")

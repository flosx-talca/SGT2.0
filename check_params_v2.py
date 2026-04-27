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
from app.models.business import ParametroLegal

app = create_app()
with app.app_context():
    params = ParametroLegal.query.all()
    print(f"Total parámetros: {len(params)}")
    for p in params:
        print(f"{p.codigo}: {p.valor} (Activo: {p.activo})")

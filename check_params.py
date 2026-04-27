import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from app import create_app
from app.models.business import ParametroLegal

app = create_app()
with app.app_context():
    params = ParametroLegal.query.all()
    print(f"Total parámetros: {len(params)}")
    for p in params[:10]:
        print(f"{p.codigo}: {p.valor} (Activo: {p.activo})")

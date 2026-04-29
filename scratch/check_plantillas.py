import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.getcwd())

from app import create_app
from app.models.business import TipoAusenciaPlantilla

app = create_app()
with app.app_context():
    tipos = TipoAusenciaPlantilla.query.all()
    print("ID | Nombre | Categoria | Tipo Restriccion")
    print("-" * 60)
    for t in tipos:
        print(f"{t.id} | {t.nombre} | {t.categoria.value} | {t.tipo_restriccion}")

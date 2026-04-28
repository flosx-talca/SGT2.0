
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from app import create_app
from app.models.business import TrabajadorAusencia, Trabajador

app = create_app()
with app.app_context():
    # Buscar ausencias en Abril 2025
    inicio_abril = datetime(2025, 4, 1).date()
    fin_abril = datetime(2025, 4, 30).date()
    
    ausencias = TrabajadorAusencia.query.filter(
        TrabajadorAusencia.fecha_inicio <= fin_abril,
        TrabajadorAusencia.fecha_fin >= inicio_abril
    ).all()
    
    print(f"Ausencias en Abril 2025 ({len(ausencias)}):")
    for a in ausencias:
        t = Trabajador.query.get(a.trabajador_id)
        nombre = f"{t.nombre} {t.apellido1}" if t else f"ID {a.trabajador_id}"
        tipo = a.tipo_ausencia.nombre if a.tipo_ausencia else "A"
        print(f"- {nombre}: {a.fecha_inicio} a {a.fecha_fin} ({tipo})")

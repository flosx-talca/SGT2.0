from app import create_app
from app.models.business import Turno

app = create_app()
with app.app_context():
    turnos = Turno.query.all()
    print(f"\n--- LISTADO DE TURNOS EN BD ({len(turnos)} en total) ---")
    for t in turnos:
        print(f"ID: {t.id} | Nombre: {t.nombre} | Empresa ID: {t.empresa_id}")
    print("---------------------------------------------------\n")

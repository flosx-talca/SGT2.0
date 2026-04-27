from app import create_app
from app.seeds.tipos_ausencia_base import seed_tipos_ausencia_base
from app.models.business import Empresa

app = create_app()
with app.app_context():
    empresas = Empresa.query.all()
    for e in empresas:
        print(f"Sembrando tipos para empresa: {e.razon_social} (ID: {e.id})")
        seed_tipos_ausencia_base(e.id)
    print("Finalizado.")

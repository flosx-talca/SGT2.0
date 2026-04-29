
from app import create_app, db
from app.models.business import ParametroLegal

app = create_app()
with app.app_context():
    parametros = ParametroLegal.query.all()
    print(f"Total parametros en BD: {len(parametros)}")
    print("-" * 50)
    for p in parametros:
        print(f"[{p.categoria}] {p.codigo} = {p.valor} ({p.descripcion})")

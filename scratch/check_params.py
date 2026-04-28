
import sys
import os

sys.path.append(os.getcwd())

from app import create_app
from app.models.business import ParametroLegal

app = create_app()
with app.app_context():
    params = ParametroLegal.query.filter(ParametroLegal.codigo.like('%MAX_HRS_SEMANA%')).all()
    for p in params:
        print(f"{p.codigo}: {p.valor}")

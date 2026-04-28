from app import create_app
from app.models.business import TrabajadorAusencia

app = create_app()
with app.app_context():
    print(f"Columns of TrabajadorAusencia: {[c.name for c in TrabajadorAusencia.__table__.columns]}")

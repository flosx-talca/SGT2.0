from app import create_app
from app.database import db
import app.models

app_instance = create_app()

with app_instance.app_context():
    print("Creando tablas en la base de datos 'sgt'...")
    db.create_all()
    print("¡Tablas creadas con éxito!")

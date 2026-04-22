from app import app
from database import db
import models

with app.app_context():
    print("Creando tablas en la base de datos 'sgt'...")
    db.create_all()
    print("¡Tablas creadas con éxito!")

from flask import Flask
from routes import init_routes
from database import db
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
# Configuración básica
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configuración Base de Datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/sgt')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar Base de Datos
db.init_app(app)

# Importar modelos para que SQLAlchemy los registre
with app.app_context():
    import models

# Inicializar rutas
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

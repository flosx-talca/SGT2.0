from flask import Flask
from routes import init_routes

app = Flask(__name__)
# Configuración básica (se puede ampliar)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Inicializar rutas
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

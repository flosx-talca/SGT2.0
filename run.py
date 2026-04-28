"""
SGT 2.1 - Ejecución de la Aplicación
-----------------------------------
Este script inicia el servidor de desarrollo de Flask.

Comandos para configurar el entorno:

Windows:
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt

Linux/macOS:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Ejecución:
    python run.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)

from app import create_app
from app.database import db
from app.models.auth import Usuario
from werkzeug.security import generate_password_hash

def reset_admin():
    app = create_app()
    with app.app_context():
        # Admin por defecto del dump
        admin = Usuario.query.filter_by(rut='99999999-9').first()
        if admin:
            admin.password_hash = generate_password_hash('1234')
            db.session.commit()
            print("Password de admin (99999999-9) reseteada a '1234'")
        else:
            print("No se encontró el usuario admin.")

if __name__ == "__main__":
    reset_admin()

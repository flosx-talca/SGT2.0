"""
migrate_tipo_preferencia.py — Script de migración para agregar columna 'tipo' a trabajador_preferencia
"""
import sys
import os

# Asegura que el proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

app = create_app()

def columna_existe(conn, tabla, columna):
    resultado = conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name   = :tabla
          AND column_name  = :columna
    """), {'tabla': tabla, 'columna': columna}).scalar()
    return resultado > 0

def migrar():
    with app.app_context():
        print("=" * 55)
        print("  Iniciando migración: campo 'tipo' en trabajador_preferencia")
        print("=" * 55)

        try:
            if columna_existe(db.session, 'trabajador_preferencia', 'tipo'):
                print("  [SKIP] Columna 'tipo' ya existe, omitida.")
            else:
                db.session.execute(text("""
                    ALTER TABLE trabajador_preferencia
                    ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'preferencia'
                """))
                db.session.execute(text("""
                    UPDATE trabajador_preferencia
                    SET tipo = 'preferencia'
                    WHERE tipo IS NULL
                """))
                db.session.commit()
                print("  [OK] Columna 'tipo' agregada exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"  [ERROR] Error: {e}")

if __name__ == '__main__':
    migrar()

"""
migrate_horas_extra.py — Script de migración para agregar columna 'permite_horas_extra' a trabajador
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
        print("  Iniciando migración: campo 'permite_horas_extra' en trabajador")
        print("=" * 55)

        try:
            if columna_existe(db.session, 'trabajador', 'permite_horas_extra'):
                print("  [SKIP] Columna 'permite_horas_extra' ya existe, omitida.")
            else:
                db.session.execute(text("""
                    ALTER TABLE trabajador
                    ADD COLUMN permite_horas_extra BOOLEAN DEFAULT FALSE
                """))
                db.session.execute(text("""
                    UPDATE trabajador
                    SET permite_horas_extra = FALSE
                    WHERE permite_horas_extra IS NULL
                """))
                db.session.commit()
                print("  [OK] Columna 'permite_horas_extra' agregada exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"  [ERROR] Error: {e}")

if __name__ == '__main__':
    migrar()

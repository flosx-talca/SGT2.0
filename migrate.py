"""
migrate.py — Script de migración manual para PostgreSQL + SQLAlchemy

Cambios que aplica:
  1. turno.es_nocturno        → agrega columna BOOLEAN NOT NULL DEFAULT FALSE
                                 y la calcula automáticamente desde hora_inicio/hora_fin
  2. trabajador.horas_semanales → rellena NULLs con 42 y aplica NOT NULL DEFAULT 42
  3. regla                    → inserta 3 reglas nuevas del scheduler si no existen:
                                   dias_descanso_post_6, jornada_semanal, duracion_turno

Uso:
  python migrate.py

Requisitos:
  - La app Flask debe estar correctamente configurada (DATABASE_URL, etc.)
  - Ejecutar desde la raíz del proyecto
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
        print("  Iniciando migración")
        print("=" * 55)

        errores = []

        # ── 1. turno.es_nocturno ─────────────────────────────────
        print("\n[1/3] Tabla turno → columna es_nocturno")
        try:
            if columna_existe(db.session, 'turno', 'es_nocturno'):
                print("  ⏭️  Ya existe, omitida.")
            else:
                db.session.execute(text("""
                    ALTER TABLE turno
                    ADD COLUMN es_nocturno BOOLEAN NOT NULL DEFAULT FALSE
                """))
                db.session.execute(text("""
                    UPDATE turno
                    SET es_nocturno = TRUE
                    WHERE hora_fin <= hora_inicio
                """))
                count = db.session.execute(text(
                    "SELECT COUNT(*) FROM turno WHERE es_nocturno = TRUE"
                )).scalar()
                db.session.commit()
                print(f"  ✅ Columna agregada. {count} turno(s) marcados como nocturnos.")
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error: {e}")
            errores.append('es_nocturno')

        # ── 2. trabajador.horas_semanales ────────────────────────
        print("\n[2/3] Tabla trabajador → horas_semanales NOT NULL DEFAULT 42")
        try:
            nulos = db.session.execute(text("""
                SELECT COUNT(*) FROM trabajador
                WHERE horas_semanales IS NULL
            """)).scalar()

            if nulos > 0:
                db.session.execute(text("""
                    UPDATE trabajador
                    SET horas_semanales = 42
                    WHERE horas_semanales IS NULL
                """))
                print(f"  ✅ {nulos} trabajador(es) sin horas actualizados a 42h.")

            db.session.execute(text("""
                ALTER TABLE trabajador
                ALTER COLUMN horas_semanales SET NOT NULL,
                ALTER COLUMN horas_semanales SET DEFAULT 42
            """))
            db.session.commit()
            print("  ✅ Columna horas_semanales: NOT NULL y DEFAULT 42 aplicados.")
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error: {e}")
            errores.append('horas_semanales')

        # ── 3. Nuevas reglas del scheduler ───────────────────────
        print("\n[3/3] Tabla regla → insertar reglas del scheduler")

        nuevas_reglas = [
            {
                'codigo':      'dias_descanso_post_6',
                'nombre':      'Días de descanso tras 6 días trabajados',
                'familia':     'descanso',
                'tipo_regla':  'hard',
                'scope':       'empresa',
                'campo':       'dias_descanso',
                'operador':    'gte',
                'params_base': '{"value": 1}',
            },
            {
                'codigo':      'jornada_semanal',
                'nombre':      'Jornada semanal por defecto (horas)',
                'familia':     'contrato',
                'tipo_regla':  'hard',
                'scope':       'empresa',
                'campo':       'horas_semanales',
                'operador':    'eq',
                'params_base': '{"value": 42}',
            },
            {
                'codigo':      'duracion_turno',
                'nombre':      'Duración estándar del turno (horas)',
                'familia':     'contrato',
                'tipo_regla':  'hard',
                'scope':       'empresa',
                'campo':       'duracion_turno',
                'operador':    'eq',
                'params_base': '{"value": 8}',
            },
        ]

        try:
            insertadas = 0
            for r in nuevas_reglas:
                existe = db.session.execute(
                    text("SELECT id FROM regla WHERE codigo = :codigo"),
                    {'codigo': r['codigo']}
                ).fetchone()

                if existe:
                    print(f"  ⏭️  '{r['codigo']}' ya existe, omitida.")
                else:
                    db.session.execute(text("""
                        INSERT INTO regla
                            (codigo, nombre, familia, tipo_regla, scope,
                             campo, operador, params_base,
                             activo, creado_en, actualizado_en)
                        VALUES
                            (:codigo, :nombre, :familia, :tipo_regla, :scope,
                             :campo, :operador, CAST(:params_base AS JSON),
                             TRUE, NOW(), NOW())
                    """), r)
                    print(f"  ✅ '{r['codigo']}' insertada.")
                    insertadas += 1

            db.session.commit()
            if insertadas > 0:
                print(f"  ✅ {insertadas} regla(s) nueva(s) insertada(s).")
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error: {e}")
            errores.append('reglas')

        # ── Resultado final ───────────────────────────────────────
        print("\n" + "=" * 55)
        if errores:
            print(f"  ⚠️  Migración completada con errores en: {', '.join(errores)}")
            print("  Revisa los mensajes de error arriba.")
            sys.exit(1)
        else:
            print("  ✅ Migración completada sin errores.")
        print("=" * 55)


if __name__ == '__main__':
    migrar()

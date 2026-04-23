import sys
import os

# Agregamos la ruta del proyecto al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.business import Regla

app_instance = create_app()

def seed_reglas():
    with app_instance.app_context():
        print("🗑️ Limpiando reglas existentes...")
        db.session.query(Regla).delete()
        db.session.commit()

        print("⚖️ Insertando reglas del Código del Trabajo (Chile)...")
        reglas = [
            Regla(
                codigo="max_weekly_hours",
                nombre="Máximo horas semanales",
                familia="comparison",
                tipo_regla="hard",
                scope="client",
                campo="trabajador.horas_semanales",
                operador="<=",
                params_base={"value": 42},
                activo=True
            ),
            Regla(
                codigo="max_daily_hours",
                nombre="Máximo horas diarias",
                familia="comparison",
                tipo_regla="hard",
                scope="client",
                campo="turno.duracion_horas",
                operador="<=",
                params_base={"value": 10},
                activo=True
            ),
            Regla(
                codigo="working_days_limit",
                nombre="Días de distribución semanal",
                familia="range",
                tipo_regla="hard",
                scope="client",
                campo="dias_trabajados_semana",
                operador="between",
                params_base={"min": 5, "max": 6},
                activo=True
            ),
            Regla(
                codigo="max_part_time_hours",
                nombre="Jornada parcial máxima",
                familia="comparison",
                tipo_regla="hard",
                scope="client",
                campo="trabajador.horas_semanales_part_time",
                operador="<=",
                params_base={"value": 30},
                activo=True
            ),
            Regla(
                codigo="sunday_compensatory_rest",
                nombre="Descanso compensatorio domingo",
                familia="calendar",
                tipo_regla="hard",
                scope="client",
                campo="domingos_trabajados",
                operador="requires_comp",
                params_base={"days_earned_per_sunday": 1},
                activo=True
            ),
            Regla(
                codigo="min_free_sundays",
                nombre="Domingos libres mínimos al mes",
                familia="comparison",
                tipo_regla="hard",
                scope="client",
                campo="domingos_libres_mes",
                operador=">=",
                params_base={"value": 2},
                activo=True
            )
        ]

        db.session.add_all(reglas)
        db.session.commit()
        
        print(f"✅ {len(reglas)} reglas insertadas con éxito.")

if __name__ == "__main__":
    seed_reglas()

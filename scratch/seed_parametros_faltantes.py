from app import create_app
from app.database import db
from app.models.business import ParametroLegal

def seed_params():
    app = create_app()
    with app.app_context():
        params = [
            # Parámetros Legales Generales
            ("MIN_HRS_TURNO_ABSOLUTO", 4.0, "Mínimo de horas por turno según ley"),
            ("MIN_HRS_TURNO_CON_COLACION", 6.0, "Mínimo de horas para tener derecho a colación"),
            ("MIN_COLACION_MIN", 30.0, "Mínimo de minutos de colación"),
            ("MAX_COLACION_MIN", 120.0, "Máximo de minutos de colación"),
            ("HORA_INICIO_NOCTURNO", 21.0, "Hora en que inicia el tramo nocturno (21:00)"),
            ("HORA_FIN_NOCTURNO", 6.0, "Hora en que termina el tramo nocturno (06:00)"),
            ("UMBRAL_DIAS_DOMINGO_OBLIGATORIO", 5.0, "Días trabajados para exigir domingos libres"),
            ("DOMINGOS_EXTRA_ANUALES_ART38BIS", 7.0, "Domingos extra al año según Art 38 Bis"),
            ("MAX_DOMINGOS_SUSTITUIBLES_SABADO", 1.0, "Domingos que pueden sustituirse por sábados"),
            ("COMP_PLAZO_DIAS_GENERAL", 15.0, "Plazo general para compensación"),
            ("COMP_PLAZO_DIAS_EXCEPTUADO", 30.0, "Plazo exceptuado para compensación"),
            ("SEMANA_CORTA_UMBRAL_DIAS", 5.0, "Umbral de días para considerar semana corta"),
            ("SEMANA_CORTA_PRORRATEO", 1.0, "1 si aplica prorrateo en semana corta, 0 si no"),
            ("ESTAB_MIN_DIAS_MISMO_TURNO", 3.0, "Mínimo de días en el mismo turno para estabilidad"),
            ("ESTAB_PENALTY_CAMBIO_TURNO", 150.0, "Penalización por cambio de turno"),
            ("ESTAB_PENALTY_TURNO_AISLADO", 200.0, "Penalización por turno aislado"),
            ("ESTAB_BONUS_TURNO_DOMINANTE", 80.0, "Bono por mantener turno dominante"),
            ("SOLVER_MAX_WORKERS", 100.0, "Máximo de trabajadores soportados por el solver"),
            ("SOFT_PENALTY_DIA_AISLADO", 500.0, "Penalización soft por día de trabajo aislado"),
            ("SOFT_PENALTY_DESCANSO_AISLADO", 300.0, "Penalización soft por día libre aislado"),
            ("SOFT_BONUS_BLOQUE_CONTINUO", 1000.0, "Bono por bloques continuos de trabajo"),
            ("PREF_MIN_DIAS_BLOQUE", 2.0, "Mínimo de días para bloque preferente"),
            ("PREF_MAX_DIAS_BLOQUE", 6.0, "Máximo de días para bloque preferente"),
            
            # Pesos del Solver (W_...)
            ("W_DEFICIT", 10_000_000.0, "Costo por turno sin cubrir (cobertura mínima)"),
            ("W_EXCESO", 100_000.0, "Costo por exceso de cobertura"),
            ("W_EQUIDAD", 1_000_000.0, "Penalización equidad mensual entre workers"),
            ("W_META", 50_000.0, "Penalización por desviarse de la meta mensual"),
            ("W_REWARD", 10_000.0, "Premio por cubrir turno requerido"),
            ("W_NOCHE_REWARD", 20_000.0, "Premio extra por cubrir turno nocturno"),
            ("W_NO_PREFERENTE", 500.0, "Penalización si no se asigna turno preferente")
        ]

        added = 0
        updated = 0
        for codigo, valor, desc in params:
            p = ParametroLegal.query.filter_by(codigo=codigo).first()
            if not p:
                p = ParametroLegal(codigo=codigo, valor=valor, descripcion=desc, categoria="Planificación")
                db.session.add(p)
                added += 1
            else:
                p.valor = valor
                p.descripcion = desc
                updated += 1
        
        db.session.commit()
        print(f"Seed finalizado: {added} agregados, {updated} actualizados.")

if __name__ == "__main__":
    seed_params()

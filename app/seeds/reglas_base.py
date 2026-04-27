from app.database import db
from app.models.business import Regla

REGLAS_BASE = [
    {
        "codigo": "max_dias_consecutivos",
        "nombre": "Maximo dias consecutivos de trabajo",
        "familia": "comparison",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "dias_consecutivos",
        "operador": "<=",
        "params_base": {"valor": 6, "fuente_parametro": "MAX_DIAS_CONSECUTIVOS"}
    },
    {
        "codigo": "no_doble_turno",
        "nombre": "No doble turno el mismo dia",
        "familia": "assignment_constraint",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "turnos_per_dia",
        "operador": "<=",
        "params_base": {"max_turnos_dia": 1}
    },
    {
        "codigo": "max_horas_semana",
        "nombre": "Limite horas semanales segun contrato",
        "familia": "comparison",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "horas_semanales",
        "operador": "<=",
        "params_base": {"fuente_parametro": "MAX_HRS_SEMANA_FULL"}
    },
    {
        "codigo": "min_descanso_semanal",
        "nombre": "Dia libre semanal obligatorio",
        "familia": "comparison",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "dias_libres_semana",
        "operador": ">=",
        "params_base": {"valor": 1, "fuente_parametro": "MIN_DESCANSO_SEMANAL_DIAS"}
    },
    {
        "codigo": "min_domingos_mes",
        "nombre": "Domingos libres minimos al mes",
        "familia": "calendar",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "domingos_libres",
        "operador": ">=",
        "params_base": {
            "fuente_parametro": "MIN_DOMINGOS_LIBRES_MES",
            "condicion": "aplica_domingo_obligatorio"
        }
    },
    {
        "codigo": "respetar_ausencias",
        "nombre": "Respetar vacaciones, licencias y permisos",
        "familia": "calendar",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "trabajador_ausencia",
        "operador": "==",
        "params_base": {"bloquear": True}
    },
    {
        "codigo": "cobertura_minima_turno",
        "nombre": "Dotacion minima requerida",
        "familia": "assignment_constraint",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "cobertura",
        "operador": ">=",
        "params_base": {"fuente": "matriz_dotacion"}
    },
    {
        "codigo": "post_noche_libre",
        "nombre": "Libre al dia siguiente de turno noche",
        "familia": "post_noche",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "es_nocturno",
        "operador": None,
        "params_base": {"condicional": True}
    },
    {
        "codigo": "prefer_bloque_continuo",
        "nombre": "Preferir bloques de trabajo continuos",
        "familia": "sequence",
        "tipo_regla": "soft",
        "scope": "client",
        "campo": "bloque_trabajo",
        "operador": None,
        "params_base": {
            "min_dias": 4,
            "max_dias": 6,
            "fuente_min": "PREF_MIN_DIAS_BLOQUE",
            "fuente_max": "PREF_MAX_DIAS_BLOQUE",
            "penalty_weight": 100
        }
    },
    {
        "codigo": "penalizar_dia_aislado",
        "nombre": "Evitar dias de trabajo aislados",
        "familia": "sequence",
        "tipo_regla": "soft",
        "scope": "client",
        "campo": "dia_aislado",
        "operador": None,
        "params_base": {"penalty_weight": 100, "fuente_penalty": "SOFT_PENALTY_DIA_AISLADO"}
    },
    {
        "codigo": "penalizar_descanso_aislado",
        "nombre": "Evitar descansos aislados",
        "familia": "sequence",
        "tipo_regla": "soft",
        "scope": "client",
        "campo": "descanso_aislado",
        "operador": None,
        "params_base": {"penalty_weight": 80, "fuente_penalty": "SOFT_PENALTY_DESCANSO_AISLADO"}
    },
    {
        "codigo": "balancear_noches",
        "nombre": "Equidad en turnos nocturnos",
        "familia": "comparison",
        "tipo_regla": "soft",
        "scope": "client",
        "campo": "turnos_noche",
        "operador": "balance",
        "params_base": {"penalty_weight": 10}
    },
    {
        "codigo": "estabilidad_turno",
        "nombre": "Favorecer estabilidad de turno",
        "familia": "sequence",
        "tipo_regla": "soft",
        "scope": "worker",
        "campo": "cambio_turno",
        "operador": None,
        "params_base": {
            "penalty_cambio": 150,
            "bonus_dominante": 80,
            "fuente_penalty": "ESTAB_PENALTY_CAMBIO_TURNO"
        }
    },
    {
        "codigo": "turno_preferente",
        "nombre": "Respetar turno preferente",
        "familia": "worker_attribute",
        "tipo_regla": "soft",
        "scope": "worker",
        "campo": "preferencia_turno",
        "operador": "==",
        "params_base": {"penalty_weight": 500, "fuente_penalty": "DEFAULT_PENALTY_NO_PREFERENTE"}
    },
    {
        "codigo": "meta_mensual_horas",
        "nombre": "Cumplimiento de meta mensual de horas",
        "familia": "comparison",
        "tipo_regla": "soft",
        "scope": "worker",
        "campo": "total_horas_mes",
        "operador": "range",
        "params_base": {"penalty_weight": 50000}
    }
]

def seed_reglas_base():
    """Inserta las 15 reglas base en la tabla 'regla'."""
    print("Seeding reglas base...")
    count = 0
    for r_data in REGLAS_BASE:
        if not Regla.query.filter_by(codigo=r_data["codigo"]).first():
            regla = Regla(
                codigo=r_data["codigo"],
                nombre=r_data["nombre"],
                familia=r_data["familia"],
                tipo_regla=r_data["tipo_regla"],
                scope=r_data["scope"],
                campo=r_data["campo"],
                operador=r_data["operador"],
                params_base=r_data["params_base"],
                activo=True
            )
            db.session.add(regla)
            count += 1
    db.session.commit()
    print(f"Hecho. Se agregaron {count} reglas.")

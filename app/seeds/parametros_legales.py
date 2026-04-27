from app.models.business import ParametroLegal
from app.database import db

PARAMETROS_INICIALES = [
    # (codigo, valor, categoria, descripcion, es_obligatorio)
    
    # Jornada Ordinaria
    ("MAX_HRS_SEMANA_FULL",             42.0, "Jornada", "Horas semanales maximas full-time (Ley 21.561)",          True),
    ("MAX_HRS_DIA_FULL",                10.0, "Jornada", "Jornada diaria maxima full-time (Art. 28 CT)",            True),
    ("MIN_DIAS_SEMANA_FULL",             5.0, "Jornada", "Dias minimos distribucion semanal full-time (Art. 28 CT)",True),
    ("MAX_DIAS_SEMANA_FULL",             6.0, "Jornada", "Dias maximos distribucion semanal full-time (Art. 28 CT)",True),
    
    # Jornada Parcial
    ("MAX_HRS_SEMANA_PART_TIME_30",     30.0, "Jornada Parcial", "Jornada parcial maxima 30h (Art. 40 bis CT)",             True),
    ("MAX_HRS_SEMANA_PART_TIME_20",     20.0, "Jornada Parcial", "Jornada reducida maxima 20h",                             True),
    ("MAX_HRS_DIA_PART_TIME",           10.0, "Jornada Parcial", "Jornada diaria maxima part-time (Art. 40 bis CT)",        True),
    ("MAX_DIAS_SEMANA_PART",             5.0, "Jornada Parcial", "Dias maximos distribucion semanal part-time",              True),
    
    # Domingos y Descansos
    ("UMBRAL_DIAS_DOMINGO_OBLIGATORIO",  5.0, "Descansos", "Dias/sem minimos para que aplique compensacion dominical", True),
    ("MIN_DOMINGOS_LIBRES_MES",          2.0, "Descansos", "Domingos libres minimos/mes cuando aplica",               True),
    ("MAX_DIAS_CONSECUTIVOS",            6.0, "Descansos", "Dias consecutivos maximos de trabajo (Art. 38 CT)",       True),
    ("MIN_DESCANSO_ENTRE_TURNOS_HRS",   12.0, "Descansos", "Horas minimas de descanso entre dos turnos",              True),
    
    # Semanas Cortas
    ("SEMANA_CORTA_UMBRAL_DIAS",         5.0, "Semanas Cortas", "Dias minimos para considerar semana completa",             True),
    ("SEMANA_CORTA_PRORRATEO",           1.0, "Semanas Cortas", "1 = prorratear horas proporcionales en semana corta",     True),

    # Solver
    ("W_CAMBIO_TURNO",                 150.0, "Optimizacion", "Penalizacion por cambio de turno entre dias",           False),
    ("W_TURNO_DOMINANTE",               80.0, "Optimizacion", "Bonus por mantener un turno dominante",                 False),
    ("W_NO_PREFERENTE",                500.0, "Optimizacion", "Penalizacion por no asignar turno preferente",          False),
]

def seed_parametros_legales():
    for codigo, valor, categoria, descripcion, es_obligatorio in PARAMETROS_INICIALES:
        p = ParametroLegal.query.filter_by(codigo=codigo).first()
        if not p:
            db.session.add(ParametroLegal(
                codigo=codigo,
                valor=valor,
                categoria=categoria,
                descripcion=descripcion,
                es_obligatorio=es_obligatorio
            ))
        else:
            # Actualizar categoria si ya existe
            p.categoria = categoria
            p.descripcion = descripcion
            
    db.session.commit()
    print("Seed de parametros legales completado.")

from app.models.business import TipoAusencia
from app.models.enums import CategoriaAusencia
from app.database import db

TIPOS_BASE = [
    # nombre,                abrev,   color,      categoria,                    tipo_restriccion
    ("Vacaciones",           "VAC",   "#3498db",  CategoriaAusencia.AUSENCIA,    None),
    ("Licencia médica",      "LM",    "#e74c3c",  CategoriaAusencia.AUSENCIA,    None),
    ("Permiso con goce",     "PCG",   "#f39c12",  CategoriaAusencia.AUSENCIA,    None),
    ("Permiso sin goce",     "PSG",   "#95a5a6",  CategoriaAusencia.AUSENCIA,    None),
    ("Día compensatorio",    "COMP",  "#9b59b6",  CategoriaAusencia.AUSENCIA,    None),
    ("Turno fijo",           "TF",    "#27ae60",  CategoriaAusencia.RESTRICCION, "turno_fijo"),
    ("Excluir turno",        "ET",    "#c0392b",  CategoriaAusencia.RESTRICCION, "excluir_turno"),
    ("Solo turno",           "ST",    "#2980b9",  CategoriaAusencia.RESTRICCION, "solo_turno"),
    ("Turno preferente",     "TP",    "#f1c40f",  CategoriaAusencia.RESTRICCION, "turno_preferente"),
    ("Post noche libre",     "PNL",   "#1abc9c",  CategoriaAusencia.RESTRICCION, "post_noche"),
]


def seed_tipos_ausencia_base(empresa_id: int):
    """
    Inserta los tipos base para una empresa.
    """
    for nombre, abrev, color, categoria, tipo_restriccion in TIPOS_BASE:
        existe = TipoAusencia.query.filter_by(
            empresa_id=empresa_id,
            abreviacion=abrev
        ).first()
        if not existe:
            db.session.add(TipoAusencia(
                empresa_id=empresa_id,
                nombre=nombre,
                abreviacion=abrev,
                color=color,
                categoria=categoria,
                tipo_restriccion=tipo_restriccion
            ))
        else:
            # Si existe, actualizamos categoría por si acaso
            existe.categoria = categoria
            existe.tipo_restriccion = tipo_restriccion
            
    db.session.commit()
    print(f"OK — Tipos de ausencia actualizados para empresa {empresa_id}")

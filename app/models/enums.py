from enum import Enum

class TipoContrato(str, Enum):
    FULL_TIME    = "full_time"
    PART_TIME_30 = "part_time_30"
    PART_TIME_20 = "part_time_20"

class CategoriaAusencia(str, Enum):
    AUSENCIA    = "ausencia"
    RESTRICCION = "restriccion"

class RestrictionType(str, Enum):
    EXCLUIR_TURNO     = "excluir_turno"     # x[w,d,t] = 0 (Hard)
    SOLO_TURNO        = "solo_turno"        # x[w,d,t] = 1 solo para t (Hard)
    TURNO_FIJO        = "turno_fijo"        # x[w,d,t] = 1 en días definidos (Hard)
    TURNO_PREFERENTE  = "turno_preferente"  # penalización si no se asigna (Soft)
    POST_NOCHE        = "post_noche"        # al día siguiente de noche, forzar libre (Hard)

NATURALEZA_POR_TIPO = {
    RestrictionType.EXCLUIR_TURNO:    "hard",
    RestrictionType.SOLO_TURNO:       "hard",
    RestrictionType.TURNO_FIJO:       "hard",
    RestrictionType.POST_NOCHE:       "hard",
    RestrictionType.TURNO_PREFERENTE: "soft",
}

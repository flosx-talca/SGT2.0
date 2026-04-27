from math import floor
from app.services.config_manager import ConfigManager
from app.models.enums import TipoContrato

MAX_HRS_MAP = {
    TipoContrato.FULL_TIME:    "MAX_HRS_SEMANA_FULL",
    TipoContrato.PART_TIME_30: "MAX_HRS_SEMANA_PART_TIME_30",
    TipoContrato.PART_TIME_20: "MAX_HRS_SEMANA_PART_TIME_20",
}

MAX_DIAS_MAP = {
    TipoContrato.FULL_TIME:    "MAX_DIAS_SEMANA_FULL",
    TipoContrato.PART_TIME_30: "MAX_DIAS_SEMANA_PART",
    TipoContrato.PART_TIME_20: "MAX_DIAS_SEMANA_PART",
}

class LegalEngine:

    @staticmethod
    def max_horas_semana(trabajador) -> float:
        """Retorna el límite legal según el contrato del trabajador."""
        codigo_param = MAX_HRS_MAP.get(trabajador.tipo_contrato, "MAX_HRS_SEMANA_FULL")
        # El límite legal real es el mínimo entre lo pactado y la ley (ej. 42h)
        limite_legal = ConfigManager.get(codigo_param, 42.0)
        return min(float(trabajador.horas_semanales), limite_legal)

    @staticmethod
    def max_horas_dia(trabajador) -> float:
        clave = "MAX_HRS_DIA_FULL" if trabajador.tipo_contrato == TipoContrato.FULL_TIME else "MAX_HRS_DIA_PART_TIME"
        return ConfigManager.get(clave, 10.0)

    @staticmethod
    def max_dias_semana_ley(trabajador) -> int:
        codigo_param = MAX_DIAS_MAP.get(trabajador.tipo_contrato, "MAX_DIAS_SEMANA_FULL")
        return ConfigManager.get_int(codigo_param, 6)

    @staticmethod
    def dias_efectivos_semana(trabajador, turno) -> int:
        """Calcula cuántos días puede trabajar el trabajador con un turno específico."""
        max_hrs = LegalEngine.max_horas_semana(trabajador)
        max_dias = LegalEngine.max_dias_semana_ley(trabajador)
        
        if not turno or turno.duracion_hrs <= 0:
            return 0
            
        # Días posibles por horas / duración del turno
        # Ej: 42h / 8.5h = 4.94 -> 4 días
        dias_por_horas = floor(max_hrs / turno.duracion_hrs)
        return min(dias_por_horas, max_dias)

    @staticmethod
    def aplica_domingo_obligatorio(trabajador, turno) -> bool:
        """Verifica si al trabajador le corresponden 2 domingos libres al mes."""
        umbral = ConfigManager.get_int("UMBRAL_DIAS_DOMINGO_OBLIGATORIO", 5)
        return LegalEngine.dias_efectivos_semana(trabajador, turno) >= umbral

    @staticmethod
    def min_domingos_libres_mes(trabajador, turno) -> int:
        if LegalEngine.aplica_domingo_obligatorio(trabajador, turno):
            return ConfigManager.get_int("MIN_DOMINGOS_LIBRES_MES", 2)
        return 0

    @staticmethod
    def es_semana_corta(dias_en_semana: int) -> bool:
        umbral = ConfigManager.get_int("SEMANA_CORTA_UMBRAL_DIAS", 5)
        return dias_en_semana < umbral

    @staticmethod
    def max_horas_semana_corta(trabajador, dias_en_semana: int) -> float:
        """Prorratea las horas si es semana corta (inicio/fin de mes)."""
        prorrateo_activo = ConfigManager.get_bool("SEMANA_CORTA_PRORRATEO", True)
        max_sem = LegalEngine.max_horas_semana(trabajador)

        if prorrateo_activo and LegalEngine.es_semana_corta(dias_en_semana):
            return round(max_sem * (dias_en_semana / 7.0), 1)
        
        return max_sem

    @staticmethod
    def resumen_legal(trabajador, turno, dias_en_semana: int = 7) -> dict:
        """Genera un diccionario con todos los límites para el Builder."""
        es_corta = LegalEngine.es_semana_corta(dias_en_semana)
        max_hrs = LegalEngine.max_horas_semana_corta(trabajador, dias_en_semana)
        
        max_dias_ley = LegalEngine.max_dias_semana_ley(trabajador)
        # Ajustar max_dias si la semana tiene menos días (ej: fin de mes tiene 3 días)
        max_dias_periodo = min(max_dias_ley, dias_en_semana)
        
        if turno and turno.duracion_hrs > 0:
            dias_efectivos = min(floor(max_hrs / turno.duracion_hrs), max_dias_periodo)
        else:
            # Si no hay turno de referencia, devolvemos el máximo legal por días
            dias_efectivos = max_dias_periodo

        return {
            "max_horas_semana": max_hrs,
            "max_dias_semana": dias_efectivos,
            "aplica_domingo": LegalEngine.aplica_domingo_obligatorio(trabajador, turno),
            "min_domingos_mes": LegalEngine.min_domingos_libres_mes(trabajador, turno),
            "max_dias_consecutivos": ConfigManager.get_int("MAX_DIAS_CONSECUTIVOS", 6),
            "min_descanso_entre_turnos": ConfigManager.get_int("MIN_DESCANSO_ENTRE_TURNOS_HRS", 12),
        }

    @staticmethod
    def turno_compatible(trabajador, turno) -> tuple[bool, str]:
        """
        Verifica si un turno es físicamente posible para el contrato del trabajador.
        Retorna (True, "") o (False, "motivo").
        """
        if not turno:
            return True, ""
            
        max_hrs_dia = LegalEngine.max_horas_dia(trabajador)
        if turno.duracion_hrs > max_hrs_dia:
            return False, f"Turno de {turno.duracion_hrs}h excede máximo diario de {max_hrs_dia}h"
            
        return True, ""

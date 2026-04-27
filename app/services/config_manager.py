from app.models.business import ParametroLegal
from app.database import db

class ConfigManager:
    _cache: dict[str, float] = {}

    @classmethod
    def preload(cls):
        """Carga todos los parámetros legales activos en caché."""
        cls.clear_cache()
        params = ParametroLegal.query.filter_by(es_activo=True).all()
        cls._cache = {p.codigo: p.valor for p in params}

    @classmethod
    def get(cls, codigo: str, default: float) -> float:
        """Obtiene un valor de configuración, prefiriendo la caché."""
        val = None
        if codigo in cls._cache:
            val = cls._cache[codigo]
        else:
            # Failsafe: buscar en BD si no está en caché
            p = ParametroLegal.query.filter_by(codigo=codigo, es_activo=True).first()
            if p:
                cls._cache[codigo] = p.valor
                val = p.valor
        
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        return default

    @classmethod
    def get_int(cls, codigo: str, default: int) -> int:
        return int(cls.get(codigo, float(default)))

    @classmethod
    def get_bool(cls, codigo: str, default: bool = True) -> bool:
        return bool(cls.get(codigo, 1.0 if default else 0.0))

    @classmethod
    def clear_cache(cls):
        """Limpia la caché de configuración."""
        cls._cache = {}

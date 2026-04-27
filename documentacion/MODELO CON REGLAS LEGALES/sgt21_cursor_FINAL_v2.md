# SGT 2.1 — Contexto completo para Cursor
## Especificación técnica, mantenedores y parámetros inteligentes

---

# PARTE 1: MANTENEDOR DE PERMISOS Y RESTRICCIONES ESPECIALES

## 1.1 Objetivo

Gestionar ausencias, permisos y restricciones individuales por trabajador.
Estas entradas son la **primera capa** que consume el Builder antes de construir el modelo CP-SAT.
El Solver nunca infiere disponibilidad: la consume como dato validado.

---

## 1.2 Entidades existentes (ya funcionan en BD)

```python
# app/models/business.py — YA EXISTE

class TipoAusencia(db.Model):
    __tablename__ = "tipo_ausencia"
    id            = db.Column(db.Integer, primary_key=True)
    empresa_id    = db.Column(db.Integer, db.ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    nombre        = db.Column(db.String(50), nullable=False)       # Ej: "Vacaciones", "Licencia"
    abreviacion   = db.Column(db.String(5),  nullable=False)       # Ej: "VAC", "LM"
    color         = db.Column(db.String(10), default="#95a5a6")
    activo        = db.Column(db.Boolean,    default=True)
    creado_en     = db.Column(db.DateTime,   default=datetime.utcnow)
    actualizado_en= db.Column(db.DateTime,   default=datetime.utcnow, onupdate=datetime.utcnow)

class TrabajadorAusencia(db.Model):
    __tablename__ = "trabajador_ausencia"
    id              = db.Column(db.Integer, primary_key=True)
    trabajador_id   = db.Column(db.Integer, db.ForeignKey("trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_inicio    = db.Column(db.Date,    nullable=False)
    fecha_fin       = db.Column(db.Date,    nullable=False)
    motivo          = db.Column(db.String(255), nullable=False, default="")
    tipo_ausencia_id= db.Column(db.Integer, db.ForeignKey("tipo_ausencia.id", ondelete="CASCADE"), nullable=True)
    tipo_ausencia   = db.relationship("TipoAusencia", lazy=True)
    creado_en       = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 1.3 Entidad nueva: `TrabajadorRestriccionTurno`

Para gestionar restricciones individuales más específicas (no ausencias de días completos).

```python
# app/models/business.py — AGREGAR

class TrabajadorRestriccionTurno(db.Model):
    __tablename__ = "trabajador_restriccion_turno"

    id            = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajador.id", ondelete="CASCADE"), nullable=False)
    empresa_id    = db.Column(db.Integer, db.ForeignKey("empresa.id",    ondelete="CASCADE"), nullable=False)

    tipo = db.Column(db.String(30), nullable=False)
    # Valores válidos:
    # "excluir_turno"     → x[w,d,t] = 0 (Hard)
    # "solo_turno"        → x[w,d,t] = 1 solo para t (Hard)
    # "turno_fijo"        → x[w,d,t] = 1 en días de semana definidos (Hard)
    # "turno_preferente"  → penalización si no se asigna ese turno (Soft)
    # "post_noche"        → al día siguiente de noche, forzar libre (Hard)

    naturaleza = db.Column(db.String(10), nullable=False)
    # Calculado automáticamente por NATURALEZA_POR_TIPO, no ingresado por usuario

    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin    = db.Column(db.Date, nullable=False)

    dias_semana  = db.Column(db.JSON, nullable=True)
    # Lista de enteros [0=lun, 1=mar, ..., 6=dom]. None = todos los días

    turno_id             = db.Column(db.Integer, db.ForeignKey("turno.id", ondelete="RESTRICT"), nullable=True)
    turno_alternativo_id = db.Column(db.Integer, db.ForeignKey("turno.id", ondelete="RESTRICT"), nullable=True)

    motivo    = db.Column(db.String(200), nullable=True)
    activo    = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    trabajador = db.relationship("Trabajador", backref=db.backref("restricciones_turno", lazy=True))
    turno      = db.relationship("Turno", foreign_keys=[turno_id], lazy=True)
    turno_alt  = db.relationship("Turno", foreign_keys=[turno_alternativo_id], lazy=True)
```

---

## 1.4 Clasificación automática Hard/Soft

```python
# app/services/legal_engine.py

NATURALEZA_POR_TIPO = {
    "excluir_turno":    "hard",
    "solo_turno":       "hard",
    "turno_fijo":       "hard",
    "post_noche":       "hard",
    "turno_preferente": "soft",
}
```

El Admin elige el tipo. El sistema asigna la naturaleza sin intervención del usuario.

---

## 1.5 Flujo del modal de restricciones (UI)

1. Admin abre modal desde el listado de trabajadores.
2. Selecciona tipo de restricción, fechas, turno, días y motivo.
3. Presiona **Guardar**.
4. Backend valida conflictos contra BD (`POST /api/restricciones/preview`).
5. Si hay error → muestra mensaje en el modal, no cierra.
6. Si éxito → inserta, refresca lista dentro del modal, limpia formulario.
7. Admin puede agregar otra restricción sin cerrar el modal.

---

## 1.6 Validaciones antes del insert

| Conflicto | Descripción |
|---|---|
| `turno_fijo` vs `turno_fijo` | Mismo trabajador, mismo día de semana, mismo período |
| `excluir_turno` vs `turno_fijo` | No se puede excluir y fijar el mismo turno |
| `solo_turno` solapado | Dos `solo_turno` activos que se solapan en fechas |
| Fechas inválidas | `fecha_fin` < `fecha_inicio` |

---

## 1.7 Traducción al Builder (CP-SAT)

```python
# app/scheduler/builder.py

for r in restricciones_activas:
    dias_aplica = [d for d in days if d in r.rango_fechas and d.weekday() in (r.dias_semana or range(7))]

    if r.tipo == "excluir_turno":
        for d in dias_aplica:
            model.Add(x[r.trabajador_id, d, r.turno_id] == 0)

    elif r.tipo in ("solo_turno", "turno_fijo"):
        for d in dias_aplica:
            model.Add(x[r.trabajador_id, d, r.turno_id] == 1)
            for t_otro in shifts:
                if t_otro.id != r.turno_id:
                    model.Add(x[r.trabajador_id, d, t_otro.id] == 0)

    elif r.tipo == "post_noche":
        for d in dias_aplica:
            d_siguiente = d + timedelta(days=1)
            if d_siguiente in days:
                for t in shifts:
                    model.Add(x[r.trabajador_id, d_siguiente, t.id] == 0)

    elif r.tipo == "turno_preferente":
        for d in dias_aplica:
            objective_terms.append(
                PENALTY_NO_PREFERENTE * (1 - x[r.trabajador_id, d, r.turno_id])
            )
```

---
---

# PARTE 2: MANTENEDOR DE PARÁMETROS INTELIGENTES

## 2.1 Arquitectura de tres capas

```
BD (parametro_legal)
    ↓ preload()
ConfigManager (caché en memoria)
    ↓ get()
LegalEngine (lógica legal encapsulada)
    ↓ resumen_legal(w, t)
Builder (restricciones CP-SAT)
```

- **BD:** Fuente única de verdad. El Super Admin edita valores desde la UI.
- **Caché:** El Solver lee solo de memoria, nunca de BD durante la ejecución.
- **Defaults en código:** Failsafe si la BD falla o la tabla está vacía.

---

## 2.2 Entidad `ParametroLegal`

```python
# app/models/business.py — AGREGAR

class ParametroLegal(db.Model):
    __tablename__ = "parametro_legal"

    id             = db.Column(db.Integer, primary_key=True)
    codigo         = db.Column(db.String(60), nullable=False, unique=True)
    # Identificador estable. NUNCA cambiar en producción.

    valor          = db.Column(db.Float, nullable=False)
    descripcion    = db.Column(db.String(255), nullable=True)

    es_activo      = db.Column(db.Boolean, default=True, nullable=False)
    # False → ConfigManager ignora este parámetro, usa default del código

    es_obligatorio = db.Column(db.Boolean, default=True, nullable=False)
    # True  → No puede desactivarse desde la UI (protección legal)
    # False → El Super Admin puede on/off según régimen del cliente

    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 2.3 Catálogo completo de variables (Seed)

```python
# app/seeds/parametros_legales.py

PARAMETROS_INICIALES = [
    # código, valor, descripcion, es_obligatorio

    # ─── JORNADA ORDINARIA ───────────────────────────────────────────────
    ("MAX_HRS_SEMANA_FULL",             42.0, "Horas semanales máximas full-time (Ley 21.561)",          True),
    ("MAX_HRS_DIA_FULL",                10.0, "Jornada diaria máxima full-time (Art. 28 CT)",            True),
    ("MIN_DIAS_SEMANA_FULL",             5.0, "Días mínimos distribución semanal full-time (Art. 28 CT)",True),
    ("MAX_DIAS_SEMANA_FULL",             6.0, "Días máximos distribución semanal full-time (Art. 28 CT)",True),

    # ─── JORNADA PARCIAL ─────────────────────────────────────────────────
    ("MAX_HRS_SEMANA_PART_TIME_30",     30.0, "Jornada parcial máxima 30h (Art. 40 bis CT)",             True),
    ("MAX_HRS_SEMANA_PART_TIME_20",     20.0, "Jornada reducida máxima 20h",                             True),
    ("MIN_HRS_SEMANA_PART_TIME",        10.0, "Mínimo horas semanales part-time válido (Art. 40 bis CT)",True),
    ("MAX_HRS_DIA_PART_TIME",           10.0, "Jornada diaria máxima part-time (Art. 40 bis CT)",        True),
    ("MIN_DIAS_SEMANA_PART",             2.0, "Días mínimos distribución semanal part-time",              True),
    ("MAX_DIAS_SEMANA_PART",             5.0, "Días máximos distribución semanal part-time",              True),

    # ─── TURNOS ──────────────────────────────────────────────────────────
    ("MIN_HRS_TURNO_ABSOLUTO",           2.0, "Mínimo de horas por turno (operativo, no legal)",         False),
    ("MIN_HRS_TURNO_CON_COLACION",       5.0, "Umbral horas turno para que colación sea obligatoria (Art. 34 CT)", True),
    ("MIN_COLACION_MIN",                30.0, "Minutos mínimos de colación cuando aplica (Art. 34 CT)",  True),
    ("MAX_COLACION_MIN",                60.0, "Minutos máximos de colación (Art. 34 CT)",                True),

    # ─── DESCANSO Y CONTINUIDAD ──────────────────────────────────────────
    ("MAX_DIAS_CONSECUTIVOS",            6.0, "Días consecutivos máximos de trabajo (Art. 38 CT)",       True),
    ("MIN_DESCANSO_ENTRE_TURNOS_HRS",   12.0, "Horas mínimas de descanso entre dos turnos consecutivos", True),
    ("MIN_DESCANSO_SEMANAL_DIAS",        1.0, "Días mínimos descanso semanal obligatorio",               True),

    # ─── DOMINGOS Y FESTIVOS ─────────────────────────────────────────────
    ("UMBRAL_DIAS_DOMINGO_OBLIGATORIO",  5.0, "Días/sem mínimos para que aplique compensación dominical (Art. 38)", True),
    ("MIN_DOMINGOS_LIBRES_MES",          2.0, "Domingos libres mínimos/mes cuando aplica (Art. 38 CT)", True),
    ("DOMINGOS_EXTRA_ANUALES_ART38BIS",  7.0, "Domingos adicionales anuales (Art. 38 bis, solo comercio)", False),
    ("MAX_DOMINGOS_SUSTITUIBLES_SABADO", 3.0, "De los 7 extras, hasta 3 pueden ser fin de semana completo sáb+dom (Art. 38 bis, con acuerdo escrito)", False),
    ("COMP_PLAZO_DIAS_GENERAL",          7.0, "Plazo días para otorgar descanso compensatorio (régimen general)", True),
    ("COMP_PLAZO_DIAS_EXCEPTUADO",      30.0, "Plazo días compensatorios (régimen exceptuado Art. 38)",  True),

    # ─── HORAS EXTRA ─────────────────────────────────────────────────────
    ("MAX_HRS_EXTRA_SEMANA",            12.0, "Horas extra máximas semanales (Art. 31 CT)",              True),
    ("RECARGO_HRS_EXTRA",                1.5, "Factor de recargo horas extra (50% sobre valor hora, Art. 32 CT)", True),

    # ─── SEMANAS CORTAS ──────────────────────────────────────────────────
    ("SEMANA_CORTA_UMBRAL_DIAS",         5.0, "Días mínimos para considerar semana completa. Menor = semana corta y se prorratean horas (Art. 28 CT: distribución 5-6 días)", True),
    ("SEMANA_CORTA_PRORRATEO",           1.0, "1 = prorratear horas proporcionales en semana corta. 0 = no ajustar", True),

    # ─── SOLVER / OPTIMIZACIÓN ───────────────────────────────────────────
    ("SOLVER_TIMEOUT_SEG",              60.0, "Timeout máximo del Solver en segundos",                   False),
    ("SOLVER_MAX_WORKERS",               4.0, "Threads máximos para OR-Tools CP-SAT",                    False),
    ("SOFT_PENALTY_DIA_AISLADO",       100.0, "Penalización función objetivo: día trabajo aislado",      False),
    ("SOFT_PENALTY_DESCANSO_AISLADO",   80.0, "Penalización función objetivo: descanso aislado",         False),
    ("SOFT_BONUS_BLOQUE_CONTINUO",      50.0, "Bonus función objetivo: bloque ≥4 días consecutivos",     False),
    ("PREF_MIN_DIAS_BLOQUE",             4.0, "Días mínimos preferidos en bloque de trabajo",             False),
    ("PREF_MAX_DIAS_BLOQUE",             6.0, "Días máximos preferidos en bloque de trabajo",             False),
]


def seed_parametros_legales():
    for codigo, valor, descripcion, es_obligatorio in PARAMETROS_INICIALES:
        if not ParametroLegal.query.filter_by(codigo=codigo).first():
            db.session.add(ParametroLegal(
                codigo=codigo,
                valor=valor,
                descripcion=descripcion,
                es_obligatorio=es_obligatorio
            ))
    db.session.commit()
```

---

## 2.4 `ConfigManager`

```python
# app/services/config_manager.py

class ConfigManager:
    _cache: dict[str, float] = {}

    @classmethod
    def preload(cls):
        """Cargar TODOS los parámetros activos antes del Builder. Una sola query."""
        params = ParametroLegal.query.filter_by(es_activo=True).all()
        cls._cache = {p.codigo: p.valor for p in params}

    @classmethod
    def get(cls, codigo: str, default: float) -> float:
        if codigo in cls._cache:
            return cls._cache[codigo]
        p = ParametroLegal.query.filter_by(codigo=codigo, es_activo=True).first()
        if p:
            cls._cache[codigo] = p.valor
            return p.valor
        return default

    @classmethod
    def get_int(cls, codigo: str, default: int) -> int:
        return int(cls.get(codigo, float(default)))

    @classmethod
    def get_bool(cls, codigo: str, default: bool = True) -> bool:
        return bool(cls.get(codigo, float(default)))

    @classmethod
    def clear_cache(cls):
        """Llamar cuando el Super Admin modifique un parámetro en la UI."""
        cls._cache = {}
```

---

## 2.5 `LegalEngine` — Lógica legal encapsulada

```python
# app/services/legal_engine.py

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
NATURALEZA_POR_TIPO = {
    "excluir_turno":    "hard",
    "solo_turno":       "hard",
    "turno_fijo":       "hard",
    "post_noche":       "hard",
    "turno_preferente": "soft",
}


class LegalEngine:

    # ── HORAS ──────────────────────────────────────────────────────────

    @staticmethod
    def max_horas_semana(trabajador) -> float:
        """Retorna el mínimo entre horas pactadas y límite legal según contrato."""
        legal   = ConfigManager.get(MAX_HRS_MAP[trabajador.tipo_contrato], 42.0)
        return min(trabajador.horas_semanales, legal)

    @staticmethod
    def max_horas_dia(trabajador) -> float:
        clave = "MAX_HRS_DIA_FULL" if trabajador.tipo_contrato == TipoContrato.FULL_TIME else "MAX_HRS_DIA_PART_TIME"
        return ConfigManager.get(clave, 10.0)

    # ── DÍAS ───────────────────────────────────────────────────────────

    @staticmethod
    def max_dias_semana_ley(trabajador) -> int:
        return ConfigManager.get_int(MAX_DIAS_MAP[trabajador.tipo_contrato], 6)

    @staticmethod
    def dias_efectivos_semana(trabajador, turno) -> int:
        """
        Días que puede trabajar este trabajador CON ESTE TURNO en una semana.

        Fórmula:
            dias = min(
                floor(max_horas_semana / turno.duracion_hrs),  ← límite por horas
                max_dias_ley                                    ← límite por contrato
            )

        IMPORTANTE: dias_efectivos NO es un campo fijo en Trabajador.
        Depende del turno asignado. Se calcula en el pre-solver.
        """
        max_hrs  = LegalEngine.max_horas_semana(trabajador)
        max_dias = LegalEngine.max_dias_semana_ley(trabajador)
        return min(floor(max_hrs / turno.duracion_hrs), max_dias)

    # ── DOMINGOS ───────────────────────────────────────────────────────

    @staticmethod
    def aplica_domingo_obligatorio(trabajador, turno) -> bool:
        """
        True si corresponden domingos libres obligatorios.
        Regla: dias_efectivos_semana >= UMBRAL (por defecto 5).

        Tabla de decisión:
            full-time,    turno 8h  → 5 días → True  → 2 dom/mes
            full-time,    turno 10h → 4 días → False → 0 dom
            part-time 30h, turno 6h → 5 días → True  → 2 dom/mes
            part-time 30h, turno 8h → 3 días → False → 0 dom
            part-time 20h, turno 4h → 5 días → True  → 2 dom/mes
            part-time 20h, turno 8h → 2 días → False → 0 dom
        """
        umbral = ConfigManager.get_int("UMBRAL_DIAS_DOMINGO_OBLIGATORIO", 5)
        return LegalEngine.dias_efectivos_semana(trabajador, turno) >= umbral

    @staticmethod
    def min_domingos_libres_mes(trabajador, turno) -> int:
        """
        Retorna 2 si aplica Art. 38, 0 si no aplica.
        Si retorna 0 → el Builder NO agrega restricción dominical → puede asignarse cualquier domingo.
        """
        if LegalEngine.aplica_domingo_obligatorio(trabajador, turno):
            return ConfigManager.get_int("MIN_DOMINGOS_LIBRES_MES", 2)
        return 0

    # ── SEMANAS CORTAS ─────────────────────────────────────────────────

    @staticmethod
    def es_semana_corta(dias_en_semana: int) -> bool:
        """
        True si la semana tiene menos días que el umbral (inicio/fin de mes).
        Ejemplo: el mes empieza jueves → esa semana tiene solo 4 días hábiles.
        """
        umbral = ConfigManager.get_int("SEMANA_CORTA_UMBRAL_DIAS", 5)
        return dias_en_semana < umbral

    @staticmethod
    def max_horas_semana_corta(trabajador, turno, dias_en_semana: int) -> float:
        """
        En semanas cortas (inicio/fin de mes), prorratear horas proporcionales
        si el parámetro SEMANA_CORTA_PRORRATEO está activo.

        Ejemplo:
            full-time 42h/semana, semana de 3 días:
            → prorrateo = 42 * (3/7) = 18h → puede trabajar hasta 2 turnos de 8h
        """
        prorrateo = ConfigManager.get_bool("SEMANA_CORTA_PRORRATEO", True)
        max_sem   = LegalEngine.max_horas_semana(trabajador)

        if prorrateo and LegalEngine.es_semana_corta(dias_en_semana):
            return round(max_sem * (dias_en_semana / 7), 1)

        return max_sem  # Sin ajuste: se aplica el máximo semanal completo

    @staticmethod
    def dias_efectivos_semana_corta(trabajador, turno, dias_en_semana: int) -> int:
        """
        Para semanas cortas, recalcula cuántos días puede trabajar
        con las horas prorrateadas.
        """
        max_hrs  = LegalEngine.max_horas_semana_corta(trabajador, turno, dias_en_semana)
        max_dias = min(LegalEngine.max_dias_semana_ley(trabajador), dias_en_semana)
        return min(floor(max_hrs / turno.duracion_hrs), max_dias)

    # ── COLACIÓN ───────────────────────────────────────────────────────

    @staticmethod
    def requiere_colacion(turno) -> bool:
        """True si el turno obliga a dar colación (Art. 34 CT)."""
        umbral = ConfigManager.get("MIN_HRS_TURNO_CON_COLACION", 5.0)
        return turno.duracion_hrs >= umbral

    # ── HORAS EXTRA ────────────────────────────────────────────────────

    @staticmethod
    def permite_horas_extra(trabajador) -> bool:
        return trabajador.permite_horas_extra

    @staticmethod
    def max_horas_extra_semana() -> float:
        return ConfigManager.get("MAX_HRS_EXTRA_SEMANA", 12.0)

    @staticmethod
    def factor_recargo_extra() -> float:
        return ConfigManager.get("RECARGO_HRS_EXTRA", 1.5)

    # ── COMPATIBILIDAD TURNO ───────────────────────────────────────────

    @staticmethod
    def turno_compatible(trabajador, turno) -> tuple[bool, str]:
        """Valida si el turno es compatible con el contrato del trabajador."""
        max_dia = LegalEngine.max_horas_dia(trabajador)
        if turno.duracion_hrs > max_dia:
            return False, f"Turno {turno.nombre} ({turno.duracion_hrs}h) excede jornada diaria máxima ({max_dia}h)"
        if LegalEngine.dias_efectivos_semana(trabajador, turno) < 1:
            return False, f"Con turno {turno.nombre} ({turno.duracion_hrs}h) el trabajador no completa ni 1 día/semana en su contrato"
        return True, ""

    # ── RESUMEN COMPLETO (entrada del Builder) ─────────────────────────

    @staticmethod
    def resumen_legal(trabajador, turno, dias_en_semana: int = 7) -> dict:
        """
        Retorna todos los parámetros legales para trabajador × turno × semana.
        El Builder SOLO llama esta función. No accede a ConfigManager directamente.
        """
        es_corta = LegalEngine.es_semana_corta(dias_en_semana)
        dias     = (LegalEngine.dias_efectivos_semana_corta(trabajador, turno, dias_en_semana)
                    if es_corta else
                    LegalEngine.dias_efectivos_semana(trabajador, turno))

        return {
            # Horas
            "max_horas_semana":       LegalEngine.max_horas_semana(trabajador),
            "max_horas_dia":          LegalEngine.max_horas_dia(trabajador),
            "horas_reales_semana":    dias * turno.duracion_hrs,

            # Días
            "max_dias_semana_ley":    LegalEngine.max_dias_semana_ley(trabajador),
            "dias_efectivos_semana":  dias,
            "es_semana_corta":        es_corta,

            # Domingos
            "aplica_domingo":         LegalEngine.aplica_domingo_obligatorio(trabajador, turno),
            "min_domingos_mes":       LegalEngine.min_domingos_libres_mes(trabajador, turno),

            # Horas extra
            "permite_horas_extra":    LegalEngine.permite_horas_extra(trabajador),
            "max_horas_extra_semana": LegalEngine.max_horas_extra_semana(),

            # Otros
            "requiere_colacion":      LegalEngine.requiere_colacion(turno),
            "max_dias_consecutivos":  ConfigManager.get_int("MAX_DIAS_CONSECUTIVOS", 6),
            "min_descanso_horas":     ConfigManager.get_int("MIN_DESCANSO_ENTRE_TURNOS_HRS", 12),
            "turno_compatible":       LegalEngine.turno_compatible(trabajador, turno),
        }
```

---

## 2.6 Semanas cortas: comportamiento del Builder

Una semana corta ocurre al inicio o fin del mes cuando el período no completa 7 días.

```
Ejemplo: mes que empieza jueves
    Semana 1 (incompleta): jue, vie, sáb, dom → 4 días
    Semana 2 a N (completas): lun a dom → 7 días
    Semana última (incompleta): puede tener 1 a 6 días
```

| Caso | Con prorrateo (`SEMANA_CORTA_PRORRATEO=1`) | Sin prorrateo (`SEMANA_CORTA_PRORRATEO=0`) |
|---|---|---|
| Full-time 42h, semana de 3 días | Máx 18h → 2 turnos de 8h | Máx 42h → 5 turnos (imposible en 3 días) |
| Part-time 20h, semana de 4 días | Máx 11.4h → 1 turno de 8h | Máx 20h → 2 turnos de 8h |

**Recomendación:** `SEMANA_CORTA_PRORRATEO = 1` (activo). El prorrateo evita que el solver intente asignar más días de los que hay disponibles en la semana.

---
---

# PARTE 3: CONTEXTO PARA CURSOR (scheduling.mdc)

## 3.1 Stack tecnológico

- **Backend:** Flask + SQLAlchemy + PostgreSQL
- **Frontend:** HTML + Bootstrap 5 + DataTables + AJAX
- **Solver:** OR-Tools CP-SAT (Python)
- **Cola de tareas:** Celery + Redis (para producción multicliente)
- **IDE:** Cursor AI

## 3.2 Modelos existentes en `business.py` (ya funcionan)

| Modelo | Tabla | Estado |
|---|---|---|
| `Cliente` | `cliente` | ✅ Funciona |
| `Empresa` | `empresa` | ✅ Funciona |
| `Servicio` | `servicio` | ✅ Funciona |
| `Turno` | `turno` | ✅ Funciona (incluye `es_nocturno`, `duracion_hrs`) |
| `TipoAusencia` | `tipo_ausencia` | ✅ Funciona |
| `Trabajador` | `trabajador` | ✅ Funciona |
| `TrabajadorPreferencia` | `trabajador_preferencia` | ✅ Funciona |
| `TrabajadorAusencia` | `trabajador_ausencia` | ✅ Funciona |
| `Regla` | `regla` | ✅ Funciona |
| `ReglaEmpresa` | `regla_empresa` | ✅ Funciona |

## 3.3 Modelos nuevos a crear (migración)

| Modelo | Tabla | Prioridad |
|---|---|---|
| `ParametroLegal` | `parametro_legal` | 🔴 Alta |
| `TrabajadorRestriccionTurno` | `trabajador_restriccion_turno` | 🔴 Alta |
| `TipoContrato` (Enum) | — campo en `Trabajador` | 🟡 Media |

## 3.4 Cambios en modelos existentes

| Modelo | Campo | Cambio |
|---|---|---|
| `Trabajador` | `tipo_contrato` | Migrar de `String` libre a `Enum` (`full_time`, `part_time_30`, `part_time_20`) |

## 3.5 Flujo del Solver (orden de ejecución)

```
1. ConfigManager.preload()             → cargar BD a memoria
2. Validar dotación y turnos           → pre-checks básicos
3. Construir restricciones de ausencias → TrabajadorAusencia → x[w,d,t] = 0
4. Construir restricciones especiales  → TrabajadorRestriccionTurno
5. Para cada (w, t, semana):
       params = LegalEngine.resumen_legal(w, t, dias_en_semana)
       → agregar restricciones CP-SAT
6. Agregar soft rules (penalizaciones)
7. solver.Solve(model)
8. Extraer asignaciones y guardar
```

## 3.6 Reglas para Cursor

- **El Builder NUNCA consulta la BD directamente.** Solo usa `LegalEngine` y `ConfigManager`.
- **`LegalEngine.resumen_legal(w, t, dias_en_semana)`** es el único punto de entrada al motor legal.
- **Si `min_domingos_mes == 0`**, no agregar restricción dominical. El trabajador puede trabajar cualquier domingo.
- **Si `turno_compatible[0] == False`**, no crear variables `x[w,d,t]` para esa combinación.
- **Semanas cortas:** siempre pasar `dias_en_semana` real al `resumen_legal`.
- **`SEMANA_CORTA_PRORRATEO`** controla si se ajustan las horas en semanas incompletas.
- **`es_obligatorio=True`** en `ParametroLegal` significa que la UI no debe mostrar opción de desactivar ese parámetro.
- **Cuando el Super Admin guarda un parámetro**, el endpoint debe llamar `ConfigManager.clear_cache()` tras el `db.session.commit()`.
- **El catálogo `PARAMETROS_INICIALES` es aditivo:** solo se agregan filas, nunca se eliminan ni cambian los `codigo`.
- **`DOMINGOS_EXTRA_ANUALES_ART38BIS`** y **`MAX_DOMINGOS_SUSTITUIBLES_SABADO`** son anuales. No modelarlos en el Solver mensual; mostrarlos como alerta administrativa al Admin.

---

## 2.7 Semanas cortas y prorrateo de horas

### Qué es prorratear

Prorratear significa dividir las horas del contrato proporcionalmente a los días disponibles en la semana:

```
horas_prorrateadas = max_horas_semana × (dias_en_semana / 7)
```

### Cuándo prorratear y cuándo no

| Días en semana | ¿Prorratear? | Razón |
|---|---|---|
| 7 | ❌ No | Semana completa, aplica contrato directo |
| 5–6 | ❌ No | Dentro del rango legal Art. 28 CT (5 a 6 días) |
| 1–4 | ✅ Sí | Semana incompleta, físicamente imposible cumplir contrato |

El umbral correcto es **5** (`SEMANA_CORTA_UMBRAL_DIAS = 5`).

### Por qué 6 días NO se prorratean

La ley dice máximo 42h distribuidas en **máximo 6 días** (Art. 28 CT).
Una semana de 6 días es perfectamente válida. Si prorrateáramos:

```
6 días con prorrateo  → 42h × 6/7 = 36h → máx 4 turnos de 8h → le quitamos 1 día sin razón ❌
6 días sin prorrateo  → 42h         → máx 5 turnos de 8h → correcto ✅
```

### Tabla de impacto por tamaño de semana (full-time 42h, turno 8h)

| Días semana | H prorrateadas | Días posibles | Tratamiento |
|---|---|---|---|
| 7 | 42h | 5 | Semana completa |
| 6 | 42h (sin prorrateo) | 5 | ✅ Normal |
| 5 | 42h (sin prorrateo) | 5 | ✅ Normal |
| 4 | 24h (con prorrateo) | 3 | ⚠️ Semana corta |
| 3 | 18h (con prorrateo) | 2 | ⚠️ Semana corta |
| 2 | 12h (con prorrateo) | 1 | 🔴 Muy corta |
| 1 | 6h  (con prorrateo) | 0 | 🔴 Sin turnos posibles |

### Implementación en `LegalEngine`

```python
@staticmethod
def es_semana_corta(dias_en_semana: int) -> bool:
    """True si la semana tiene menos de UMBRAL días (default 5)."""
    umbral = ConfigManager.get_int("SEMANA_CORTA_UMBRAL_DIAS", 5)  # ← 5, no 4
    return dias_en_semana < umbral

@staticmethod
def max_horas_semana_corta(trabajador, turno, dias_en_semana: int) -> float:
    """
    Si es semana corta y SEMANA_CORTA_PRORRATEO=1 → prorratear.
    Si es semana normal (≥5 días) → retornar max_horas_semana sin ajuste.
    """
    prorrateo = ConfigManager.get_bool("SEMANA_CORTA_PRORRATEO", True)
    max_sem   = LegalEngine.max_horas_semana(trabajador)

    if prorrateo and LegalEngine.es_semana_corta(dias_en_semana):
        return round(max_sem * (dias_en_semana / 7), 1)

    return max_sem  # ← semana de 5, 6 o 7 días: sin ajuste
```

### Implementación de `dividir_en_semanas` con `calendar`

```python
# app/scheduler/builder.py

import calendar
from datetime import date, timedelta

def dividir_en_semanas(fecha_inicio: date, fecha_fin: date) -> list[list[date]]:
    """
    Usa calendar.weekday() para dividir el rango en semanas ISO (lun→dom).
    Detecta automáticamente semanas cortas al inicio y fin del período.

    Ejemplo: período 1→31 mayo 2025
        Semana 1: [jue 1, vie 2, sáb 3, dom 4]       → 4 días → corta → prorratear
        Semana 2: [lun 5 ... dom 11]                  → 7 días → normal
        ...
        Semana 5: [lun 26 ... sáb 31]                 → 6 días → normal (NO prorratear)
    """
    semanas = []
    dia = fecha_inicio

    while dia <= fecha_fin:
        inicio_semana = dia - timedelta(days=calendar.weekday(dia.year, dia.month, dia.day))
        fin_semana    = inicio_semana + timedelta(days=6)
        inicio_real   = max(inicio_semana, fecha_inicio)
        fin_real      = min(fin_semana,    fecha_fin)
        semana        = [inicio_real + timedelta(days=i)
                         for i in range((fin_real - inicio_real).days + 1)]
        semanas.append(semana)
        dia = fin_semana + timedelta(days=1)

    return semanas
```

### Lo que el Builder hace por semana

```python
for semana in semanas:
    dias_en_semana = len(semana)  # calendar lo calculó automáticamente

    for w in workers:
        for t in shifts:
            params   = LegalEngine.resumen_legal(w, t, dias_en_semana)
            dias_max = params["dias_efectivos_semana"]

            # El Solver sabe cuántos días puede asignar en esta semana específica
            model.Add(
                sum(x[w.id, d, t.id] for d in semana) <= dias_max
            )
```

El Admin solo define `fecha_inicio` y `fecha_fin`. El Builder detecta semanas cortas solo con `calendar` y ajusta las restricciones automáticamente. Cero intervención manual.

---

---
---

# PARTE 4: CATÁLOGO DE REGLAS BASE (Seed tabla `regla`)

## 4.1 Propósito

Estas reglas se insertan en la tabla `regla` como datos iniciales.
El Builder **nunca las hardcodea**: las lee desde BD, identifica su familia y ejecuta el evaluador genérico.
Agregar una regla nueva = INSERT en BD. No tocar código.

---

## 4.2 Catálogo inicial

| Código | Familia | Tipo | Scope | Descripción |
|---|---|---|---|---|
| `max_dias_consecutivos` | `comparison` | hard | client | Máx 6 días seguidos (Art. 38 CT) |
| `no_doble_turno` | `assignment_constraint` | hard | client | No 2 turnos el mismo día |
| `max_horas_semana` | `comparison` | hard | worker | Límite semanal según contrato |
| `max_horas_dia` | `comparison` | hard | worker | Límite diario según contrato |
| `min_descanso_semanal` | `comparison` | hard | client | Al menos 1 día libre por semana |
| `min_domingos_mes` | `calendar` | hard | worker | 2 domingos libres/mes si aplica Art. 38 |
| `respetar_ausencias` | `calendar` | hard | worker | Bloquear días de vacaciones/licencia/permiso |
| `turno_area_permitida` | `worker_attribute` | hard | worker | Solo asignar turnos del área autorizada |
| `cobertura_minima_turno` | `assignment_constraint` | hard | client | Dotación mínima requerida por turno |
| `post_noche_libre` | `post_noche` | hard | worker | Libre al día siguiente de noche si no repite noche |
| `prefer_bloque_continuo` | `sequence` | soft | client | Preferir bloques de 4–6 días consecutivos |
| `penalizar_dia_aislado` | `sequence` | soft | client | Evitar día suelto de trabajo entre libres |
| `penalizar_descanso_aislado` | `sequence` | soft | client | Evitar día libre aislado entre trabajo |
| `balancear_noches` | `comparison` | soft | client | Distribuir turnos noche equitativamente |
| `turno_preferente` | `worker_attribute` | soft | worker | Respetar preferencia de turno del trabajador |

---

## 4.3 Ejemplos de `params_base` por regla

```python
# Seeds para tabla `regla`

REGLAS_BASE = [
    {
        "codigo": "max_dias_consecutivos",
        "nombre": "Máximo días consecutivos de trabajo",
        "familia": "comparison",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "dias_consecutivos",
        "operador": "<=",
        "params_base": {"valor": 6, "fuente_parametro": "MAX_DIAS_CONSECUTIVOS"}
        # fuente_parametro → el Builder lee el valor desde ConfigManager, no hardcodeado
    },
    {
        "codigo": "no_doble_turno",
        "nombre": "No doble turno el mismo día",
        "familia": "assignment_constraint",
        "tipo_regla": "hard",
        "scope": "client",
        "campo": "turnos_por_dia",
        "operador": "<=",
        "params_base": {"max_turnos_dia": 1}
    },
    {
        "codigo": "min_domingos_mes",
        "nombre": "Domingos libres mínimos al mes",
        "familia": "calendar",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "domingos_libres",
        "operador": ">=",
        "params_base": {
            "fuente_parametro": "MIN_DOMINGOS_LIBRES_MES",
            "condicion": "aplica_domingo_obligatorio"
            # Si LegalEngine.aplica_domingo_obligatorio == False → regla se omite
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
        "codigo": "post_noche_libre",
        "nombre": "Libre al día siguiente de turno noche (si no repite noche)",
        "familia": "post_noche",
        "tipo_regla": "hard",
        "scope": "worker",
        "campo": "es_nocturno",
        "operador": None,
        "params_base": {
            "condicional": True,
            # True = solo aplica si el día siguiente NO es también turno noche
            # False = siempre dar libre después de noche
        }
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
            "penalty_weight": 100,
            "fuente_penalty": "SOFT_PENALTY_DIA_AISLADO"
        }
    },
]
```

---
---

# PARTE 5: CÓMO AGREGAR REGLAS NUEVAS

## 5.1 El principio

El Builder **nunca interpreta la ley directamente**.
Todas las reglas se declaran en BD y el motor genérico las ejecuta.
Esto significa que agregar una regla nueva **raramente requiere tocar código**.

---

## 5.2 Los 3 casos posibles

### Caso 1: Regla con familia existente → solo BD
**No tocas ningún archivo de código.**

```
Familia existente: comparison, range, calendar, sequence,
                   set_membership, assignment_constraint,
                   worker_attribute, post_noche, logic_all_any_not
```

Ejemplo: quieres limitar a 3 turnos noche por semana.

```python
# Solo INSERT en BD:
{
    "codigo": "max_noches_semana",
    "familia": "comparison",      # ← ya existe
    "tipo_regla": "hard",
    "scope": "client",
    "campo": "turnos_noche_semana",
    "operador": "<=",
    "params_base": {"valor": 3}
}
```

**Frontend: ❌ no tocar. Builder: ❌ no tocar. Solver: ❌ no tocar.**

---

### Caso 2: Familia nueva (lógica nueva) → BD + una función + un elif
Solo cuando la lógica no encaja en ninguna familia existente.

```python
# 1. INSERT en BD con la nueva familia
{"codigo": "nueva_regla", "familia": "mi_familia_nueva", ...}

# 2. Una función nueva en LegalEngine o builder.py
def aplicar_mi_familia_nueva(model, x, workers, days, shifts, regla):
    params = regla.params_base
    # ... lógica CP-SAT ...

# 3. Un elif en el dispatcher del Builder
elif regla.familia == "mi_familia_nueva":
    aplicar_mi_familia_nueva(model, x, workers, days, shifts, regla)
```

**Frontend: ❌ no tocar. Solver: ❌ no tocar.**

---

### Caso 3: Nuevo tipo de contrato → BD + Enum + mapa
Solo cuando hay un contrato laboral nuevo (ej: jornada de 35h).

```python
# 1. INSERT en parametro_legal
("MAX_HRS_SEMANA_PART_TIME_35", 35.0, "Nueva jornada 35h")

# 2. Agregar al Enum
class TipoContrato(str, Enum):
    PART_TIME_35 = "part_time_35"   # ← nuevo

# 3. Agregar al mapa en LegalEngine
MAX_HRS_MAP[TipoContrato.PART_TIME_35] = "MAX_HRS_SEMANA_PART_TIME_35"

# 4. Frontend: agregar opción en el selector de tipo de contrato
```

---

## 5.3 Regla de oro para Cursor

```
¿La lógica ya existe en alguna familia?
    Sí → solo INSERT en BD
    No → una función + un elif + INSERT en BD

¿Cambia un valor legal (horas, días, umbrales)?
    → solo UPDATE en parametro_legal + ConfigManager.clear_cache()

¿Nuevo tipo de contrato?
    → INSERT param + Enum + mapa + opción frontend
```

---

## 5.4 Ejemplo completo: agregar "post_noche condicional"

> Regla: si el trabajador hizo turno noche, darle libre al día siguiente **a menos que el día siguiente también sea turno noche**.

```python
# Paso 1: INSERT en BD (familia nueva "post_noche_condicional")
{
    "codigo":     "post_noche_libre_condicional",
    "familia":    "post_noche_condicional",
    "tipo_regla": "hard",
    "scope":      "worker",
    "params_base": {"condicional": True}
}

# Paso 2: función en builder.py
def aplicar_post_noche_condicional(model, x, workers, days, shifts):
    turno_noche_ids = [t.id for t in shifts if t.es_nocturno]

    for w in workers:
        for i, d in enumerate(days[:-1]):
            d_sig = days[i + 1]
            for t_noche in turno_noche_ids:
                hizo_noche = x[w.id, d, t_noche]

                hace_noche_sig = model.NewBoolVar(f"noche_sig_{w.id}_{i}")
                model.Add(
                    sum(x[w.id, d_sig, tn] for tn in turno_noche_ids) >= 1
                ).OnlyEnforceIf(hace_noche_sig)
                model.Add(
                    sum(x[w.id, d_sig, tn] for tn in turno_noche_ids) == 0
                ).OnlyEnforceIf(hace_noche_sig.Not())

                dia_libre = 1 - sum(x[w.id, d_sig, t.id] for t in shifts)
                model.Add(dia_libre == 1).OnlyEnforceIf([
                    hizo_noche,
                    hace_noche_sig.Not()
                ])

# Paso 3: elif en el dispatcher
elif regla.familia == "post_noche_condicional":
    aplicar_post_noche_condicional(model, x, workers, days, shifts)
```

**Resultado: 0 cambios en frontend, 0 cambios en el Solver, 1 función + 1 elif + 1 INSERT.**

---

> **Nota final para Cursor:** Antes de implementar cualquier regla nueva, verificar si su lógica encaja en una familia existente. El 80% de las reglas nuevas serán solo un INSERT en BD.

---
---

# PARTE 6: ESTABILIDAD DE TURNO (Cuadrante legible y predecible)

## 6.1 El problema

Sin restricciones de estabilidad, el Solver puede generar calendarios válidos pero caóticos:

```
❌ MAL (válido legalmente pero ilegible):
Trabajador   L   M   M   J   V   S   D
Juan         M   N   T   I   L   M   N

✅ BIEN (estable, legible, predecible):
Trabajador   L   M   M   J   V   S   D
Juan         M   M   M   T   T   L   L
```

El objetivo es que cada trabajador tenga **bloques homogéneos de turno**, no una mezcla diaria.

---

## 6.2 Concepto: estabilidad de turno

Un cuadrante es **estable** cuando:
1. Un trabajador trabaja el mismo turno la mayoría de sus días activos.
2. Si hay cambio de turno, ocurre en bloque (3+ días del mismo turno, luego cambia).
3. Nunca alterna turno día a día (M, N, T, M, N = inaceptable).

---

## 6.3 Parámetros nuevos en `ParametroLegal`

```python
# Agregar al seed PARAMETROS_INICIALES:

("ESTAB_MIN_DIAS_MISMO_TURNO",   3.0, "Días mínimos consecutivos en el mismo turno por bloque"),
("ESTAB_PENALTY_CAMBIO_TURNO", 150.0, "Penalización por cada cambio de turno entre días consecutivos"),
("ESTAB_PENALTY_TURNO_AISLADO",200.0, "Penalización por día en un turno distinto al bloque principal"),
("ESTAB_BONUS_TURNO_DOMINANTE", 80.0, "Bonus si el trabajador tiene un turno dominante ≥50% del período"),
```

---

## 6.4 Implementación en el Builder (CP-SAT)

### Estrategia 1: Penalizar cambios de turno entre días consecutivos

```python
# Para cada trabajador, penalizar cada vez que cambia de turno entre día d y d+1

for w in workers:
    for i, d in enumerate(days[:-1]):
        d_sig = days[i + 1]

        for t in shifts:
            # cambio_turno[w,d,t] = 1 si trabajó turno t en día d
            #                         pero NO trabajó turno t en día d+1
            cambio = model.NewBoolVar(f"cambio_{w.id}_{i}_{t.id}")

            trabajó_hoy      = x[w.id, d,     t.id]
            no_trabajó_mañana = 1 - x[w.id, d_sig, t.id]

            # cambio = 1 si trabajó hoy ese turno Y mañana no
            model.AddMultiplicationEquality(cambio, [trabajó_hoy, no_trabajó_mañana])

            penalty = ConfigManager.get_int("ESTAB_PENALTY_CAMBIO_TURNO", 150)
            objective_terms.append(penalty * cambio)
```

### Estrategia 2: Penalizar días aislados en un turno distinto al bloque

```python
# Para cada trabajador, detectar si un día tiene un turno distinto
# al turno de los días anterior y posterior (día "intruso")

for w in workers:
    for i, d in enumerate(days[1:-1]):   # excluir primero y último
        d_ant = days[i]
        d_sig = days[i + 2]

        for t in shifts:
            for t_otro in shifts:
                if t.id == t_otro.id:
                    continue

                # intruso[w,d,t] = 1 si:
                # - ayer trabajó turno t
                # - hoy  trabajó turno t_otro (distinto)
                # - mañana trabajó turno t (vuelve al anterior)
                intruso = model.NewBoolVar(f"intruso_{w.id}_{i}_{t.id}_{t_otro.id}")

                model.AddBoolAnd([
                    x[w.id, d_ant, t.id],
                    x[w.id, d,     t_otro.id],
                    x[w.id, d_sig, t.id],
                ]).OnlyEnforceIf(intruso)

                penalty = ConfigManager.get_int("ESTAB_PENALTY_TURNO_AISLADO", 200)
                objective_terms.append(penalty * intruso)
```

### Estrategia 3: Bonus por turno dominante

```python
# Si el trabajador tiene un turno que usa ≥ 50% de sus días trabajados → bonus

for w in workers:
    total_dias_trabajo = sum(x[w.id, d, t.id] for d in days for t in shifts)

    for t in shifts:
        dias_en_turno_t = sum(x[w.id, d, t.id] for d in days)

        # es_dominante = 1 si días_en_turno_t >= total_dias_trabajo / 2
        es_dominante = model.NewBoolVar(f"dominante_{w.id}_{t.id}")
        model.Add(dias_en_turno_t * 2 >= total_dias_trabajo).OnlyEnforceIf(es_dominante)

        bonus = ConfigManager.get_int("ESTAB_BONUS_TURNO_DOMINANTE", 80)
        objective_terms.append(-bonus * es_dominante)  # negativo = bonus
```

---

## 6.5 Regla en catálogo (BD)

```python
# Agregar a REGLAS_BASE:

{
    "codigo":     "estabilidad_turno",
    "nombre":     "Estabilidad de turno (cuadrante legible)",
    "familia":    "sequence",
    "tipo_regla": "soft",
    "scope":      "client",
    "campo":      "secuencia_turno",
    "operador":   None,
    "params_base": {
        "min_dias_mismo_turno":  3,
        "fuente_penalty_cambio": "ESTAB_PENALTY_CAMBIO_TURNO",
        "fuente_penalty_aislado":"ESTAB_PENALTY_TURNO_AISLADO",
        "fuente_bonus_dominante":"ESTAB_BONUS_TURNO_DOMINANTE",
    }
},
```

---

## 6.6 Resultado esperado en el cuadrante

Con estas penalizaciones activas, el Solver naturalmente preferirá:

```
✅ ESTABLE:
Juan     M  M  M  M  T  T  L  L  M  M  M  T  T  T  L  L ...
Ana      T  T  T  T  T  L  L  T  T  T  T  T  L  L  T  T ...
Pedro    N  N  N  L  L  N  N  N  N  L  L  N  N  N  L  L ...

❌ EVITADO (penalizado):
Juan     M  N  T  M  I  L  T  N  M  T  I  M  N  T  L  M ...
```

---

## 6.7 Tensión con la cobertura

El Solver debe equilibrar estabilidad con cobertura. Si la dotación es justa,
puede que para cubrir todos los turnos deba romper la estabilidad en algunos días.

La solución es configurar los pesos correctamente:

| Situación | Ajuste |
|---|---|
| Cuadrante muy mezclado | Subir `ESTAB_PENALTY_CAMBIO_TURNO` (ej: 200 → 400) |
| Cobertura no se cumple | Bajar `ESTAB_PENALTY_CAMBIO_TURNO` para dar más flexibilidad |
| Trabajador con turno fijo | Usar `TrabajadorRestriccionTurno` tipo `turno_fijo` → Hard rule, no penalización |

El Super Admin puede ajustar estos pesos desde el mantenedor de `ParametroLegal` sin tocar código.

---

## 6.8 Regla de oro para la estabilidad

```
Turno preferido conocido  → TrabajadorRestriccionTurno tipo "turno_preferente" (soft, penalización)
Turno fijo obligatorio    → TrabajadorRestriccionTurno tipo "turno_fijo"        (hard, = 1)
Estabilidad general       → ESTAB_PENALTY_CAMBIO_TURNO + ESTAB_PENALTY_TURNO_AISLADO (soft, parámetro)
```

Las tres capas conviven sin conflicto porque todas son restricciones al mismo modelo CP-SAT.
El Solver encuentra el balance óptimo entre estabilidad, cobertura y restricciones individuales.

---
---

# PARTE 7: PLAN DE IMPLEMENTACIÓN

## 7.1 Orden de ejecución

Seguir este orden estrictamente. Cada paso depende del anterior.

```
Paso 1 → business.py          (modelos nuevos en BD)
Paso 2 → migración Flask       (crear tablas)
Paso 3 → enums.py              (TipoContrato)
Paso 4 → config_manager.py    (caché de parámetros)
Paso 5 → legal_engine.py      (lógica legal encapsulada)
Paso 6 → seeds/parametros_legales.py  (datos iniciales)
Paso 7 → seeds/reglas_base.py         (reglas iniciales)
Paso 8 → builder.py           (construcción del modelo CP-SAT)
Paso 9 → scheduling_service.py (orquestador del proceso)
```

---

## 7.2 Paso 1 — `app/models/business.py`

**Qué tiene ahora (NO tocar):**
- `Cliente`, `Empresa`, `Servicio`, `Turno`, `TipoAusencia`
- `Trabajador`, `TrabajadorPreferencia`, `TrabajadorAusencia`
- `Regla`, `ReglaEmpresa`

**Qué agregar:**

```python
# 1. Nueva tabla de parámetros legales
class ParametroLegal(db.Model): ...        # ver Parte 2.2

# 2. Nueva tabla de restricciones especiales de turno
class TrabajadorRestriccionTurno(db.Model): ...  # ver Parte 1.3

# 3. Modificar Trabajador: tipo_contrato de String → Enum
# tipo_contrato = db.Column(db.String(50)...)  ← cambiar a:
# tipo_contrato = db.Column(db.Enum(TipoContrato)...)
```

---

## 7.3 Paso 2 — Migración Flask

```bash
flask db migrate -m "add_parametro_legal_restriccion_turno"
flask db upgrade
```

Verificar que se crearon las tablas:
- `parametro_legal`
- `trabajador_restriccion_turno`
- Columna `tipo_contrato` migrada a Enum en `trabajador`

---

## 7.4 Paso 3 — `app/models/enums.py` (archivo nuevo)

```python
from enum import Enum

class TipoContrato(str, Enum):
    FULL_TIME    = "full_time"
    PART_TIME_30 = "part_time_30"
    PART_TIME_20 = "part_time_20"

NATURALEZA_POR_TIPO_RESTRICCION = {
    "excluir_turno":    "hard",
    "solo_turno":       "hard",
    "turno_fijo":       "hard",
    "post_noche":       "hard",
    "turno_preferente": "soft",
}
```

---

## 7.5 Paso 4 — `app/services/config_manager.py` (archivo nuevo)

Ver implementación completa en **Parte 2.4**.

Puntos clave:
- `preload()` → carga toda la tabla `parametro_legal` de una vez
- `get()` / `get_int()` / `get_bool()` → lectura desde caché
- `clear_cache()` → llamar cuando Super Admin edita un parámetro

---

## 7.6 Paso 5 — `app/services/legal_engine.py` (archivo nuevo)

Ver implementación completa en **Parte 2.5**.

Funciones que expone al Builder:
- `max_horas_semana(w)` → horas máximas según contrato
- `max_horas_dia(w)` → límite diario
- `dias_efectivos_semana(w, t)` → días posibles según turno × contrato
- `aplica_domingo_obligatorio(w, t)` → True/False
- `min_domingos_libres_mes(w, t)` → 0 o 2
- `es_semana_corta(n)` → True si < 5 días
- `max_horas_semana_corta(w, t, n)` → horas prorrateadas
- `turno_compatible(w, t)` → (bool, motivo)
- `resumen_legal(w, t, dias)` → dict completo para el Builder

---

## 7.7 Paso 6 — `app/seeds/parametros_legales.py` (archivo nuevo)

Ver catálogo completo en **Parte 2.3** (36 variables).

Ejecutar con:
```python
# En flask shell o CLI
from app.seeds.parametros_legales import seed_parametros_legales
seed_parametros_legales()
```

---

## 7.8 Paso 7 — `app/seeds/reglas_base.py` (archivo nuevo)

Ver catálogo en **Parte 4.3** (15 reglas).

```python
def seed_reglas_base():
    for r in REGLAS_BASE:
        if not Regla.query.filter_by(codigo=r["codigo"]).first():
            db.session.add(Regla(**r))
    db.session.commit()
```

---

## 7.9 Paso 8 — `app/scheduler/builder.py` (archivo nuevo o refactor)

Estructura interna del Builder:

```python
def build_model(fecha_inicio, fecha_fin, empresa_id):

    # ── 1. Cargar parámetros desde BD → caché ─────────────────
    ConfigManager.preload()

    # ── 2. Cargar datos ───────────────────────────────────────
    workers  = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).all()
    shifts   = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    days     = [fecha_inicio + timedelta(i) for i in range((fecha_fin - fecha_inicio).days + 1)]
    semanas  = dividir_en_semanas(fecha_inicio, fecha_fin)  # usa calendar

    # ── 3. Pre-validaciones ───────────────────────────────────
    incompatibles = []
    for w in workers:
        for t in shifts:
            ok, motivo = LegalEngine.turno_compatible(w, t)
            if not ok:
                incompatibles.append({"trabajador": w.nombre, "turno": t.nombre, "motivo": motivo})
    if incompatibles:
        return {"status": "warning", "incompatibles": incompatibles}

    # ── 4. Crear variables CP-SAT ─────────────────────────────
    model = cp_model.CpModel()
    x = {}
    for w in workers:
        for d in days:
            for t in shifts:
                x[w.id, d, t.id] = model.NewBoolVar(f"x_{w.id}_{d}_{t.id}")

    objective_terms = []

    # ── 5. Restricciones de ausencias (Hard) ──────────────────
    # TrabajadorAusencia → x[w,d,t] = 0 en días bloqueados

    # ── 6. Restricciones especiales (Hard/Soft) ───────────────
    # TrabajadorRestriccionTurno → excluir, fijo, post_noche, preferente

    # ── 7. Restricciones legales por semana (Hard) ────────────
    for semana in semanas:
        dias_n = len(semana)
        for w in workers:
            for t in shifts:
                params   = LegalEngine.resumen_legal(w, t, dias_n)
                dias_max = params["dias_efectivos_semana"]
                model.Add(
                    sum(x[w.id, d, t.id] for d in semana) <= dias_max
                )
                if params["aplica_domingo"]:
                    domingos = [d for d in semana if d.weekday() == 6]
                    if domingos:
                        model.Add(
                            sum(1 - sum(x[w.id, d, tt.id] for tt in shifts) for d in domingos)
                            >= params["min_domingos_mes"]
                        )

    # ── 8. Cobertura mínima por turno (Hard) ──────────────────
    for d in days:
        for t in shifts:
            model.Add(
                sum(x[w.id, d, t.id] for w in workers) >= t.dotacion_diaria
            )

    # ── 9. No doble turno (Hard) ──────────────────────────────
    for w in workers:
        for d in days:
            model.Add(sum(x[w.id, d, t.id] for t in shifts) <= 1)

    # ── 10. Estabilidad de turno (Soft) ───────────────────────
    # Ver Parte 6.4: penalizar cambios + días intrusos + bonus dominante

    # ── 11. Preferir bloques continuos (Soft) ─────────────────
    # Ver Parte 3.6: SOFT_PENALTY_DIA_AISLADO, SOFT_BONUS_BLOQUE_CONTINUO

    # ── 12. Función objetivo ──────────────────────────────────
    model.Minimize(sum(objective_terms))

    # ── 13. Resolver ──────────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = ConfigManager.get_int("SOLVER_TIMEOUT_SEG", 60)
    solver.parameters.num_search_workers  = ConfigManager.get_int("SOLVER_MAX_WORKERS", 4)
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "ok", "asignaciones": extraer_asignaciones(solver, x, workers, days, shifts)}
    else:
        return {"status": "infeasible", "mensaje": "No se encontró solución factible"}
```

---

## 7.10 Paso 9 — `app/services/scheduling_service.py`

Orquestador del proceso. Lo llama la ruta Flask.

```python
# app/services/scheduling_service.py

from app.scheduler.builder import build_model
from app.services.config_manager import ConfigManager

class SchedulingService:

    @staticmethod
    def run(empresa_id: int, fecha_inicio, fecha_fin) -> dict:
        # 1. Limpiar caché para asegurar parámetros frescos
        ConfigManager.clear_cache()

        # 2. Construir y resolver
        resultado = build_model(fecha_inicio, fecha_fin, empresa_id)

        # 3. Si hay solución, guardar en BD
        if resultado["status"] == "ok":
            SchedulingService._guardar_asignaciones(resultado["asignaciones"])

        return resultado

    @staticmethod
    def _guardar_asignaciones(asignaciones):
        # INSERT en tabla planificacion_asignacion
        # ... implementar según modelo de datos ...
        pass
```

---

## 7.11 Checklist de implementación

```
□ Paso 1: Agregar ParametroLegal y TrabajadorRestriccionTurno en business.py
□ Paso 2: flask db migrate + flask db upgrade
□ Paso 3: Crear app/models/enums.py con TipoContrato
□ Paso 4: Crear app/services/config_manager.py
□ Paso 5: Crear app/services/legal_engine.py
□ Paso 6: Crear app/seeds/parametros_legales.py + ejecutar seed
□ Paso 7: Crear app/seeds/reglas_base.py + ejecutar seed
□ Paso 8: Crear app/scheduler/builder.py
□ Paso 9: Crear app/services/scheduling_service.py
□ Validar: correr un test con empresa de prueba y período de 1 semana
□ Validar: verificar que semanas cortas se detectan correctamente
□ Validar: verificar que cuadrante muestra bloques estables de turno
```

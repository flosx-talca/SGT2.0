# SGT 2.1 — Especificación técnica para Antigravity
## Correcciones del motor de planificación (builder)

**Fecha:** Abril 2026
**Prioridad:** Alta
**Alcance:** Cambios mínimos y quirúrgicos. No agregar funcionalidades nuevas.
**Al terminar:** Entregar resumen de exactamente qué se modificó en cada archivo.

---

## REGLA GENERAL

> Modificar **solo** lo que se indica en este documento.
> No refactorizar, no renombrar variables, no cambiar lógica que no se mencione.
> Si algo no está en este documento → no tocarlo.

---

## CAMBIO 1 — Seed de parámetros legales faltantes

### Archivo a modificar
`seed_oficial.py` (o el equivalente en `app/seeds/`)

### Qué hacer
Ejecutar el archivo `seed_parametros_faltantes.py` adjunto como parte del seed oficial.
Integrar su contenido en el seed principal para que corra con `flask seed-all`.

Los parámetros a agregar son exactamente los del archivo adjunto:
```
MIN_HRS_TURNO_ABSOLUTO, MIN_HRS_TURNO_CON_COLACION, MIN_COLACION_MIN,
MAX_COLACION_MIN, HORA_INICIO_NOCTURNO, HORA_FIN_NOCTURNO,
UMBRAL_DIAS_DOMINGO_OBLIGATORIO, DOMINGOS_EXTRA_ANUALES_ART38BIS,
MAX_DOMINGOS_SUSTITUIBLES_SABADO, COMP_PLAZO_DIAS_GENERAL,
COMP_PLAZO_DIAS_EXCEPTUADO, SEMANA_CORTA_UMBRAL_DIAS,
SEMANA_CORTA_PRORRATEO, ESTAB_MIN_DIAS_MISMO_TURNO,
ESTAB_PENALTY_CAMBIO_TURNO, ESTAB_PENALTY_TURNO_AISLADO,
ESTAB_BONUS_TURNO_DOMINANTE, SOLVER_MAX_WORKERS,
SOFT_PENALTY_DIA_AISLADO, SOFT_PENALTY_DESCANSO_AISLADO,
SOFT_BONUS_BLOQUE_CONTINUO, PREF_MIN_DIAS_BLOQUE, PREF_MAX_DIAS_BLOQUE
```

Además agregar estos que faltan y no están en ningún seed:
```python
("W_DEFICIT",       10_000_000.0, "Costo por turno sin cubrir (cobertura mínima)",       True),
("W_EXCESO",           100_000.0, "Costo por exceso de cobertura",                        True),
("W_EQUIDAD",        1_000_000.0, "Penalización equidad mensual entre workers",           False),
("W_META",              50_000.0, "Penalización por desviarse de la meta mensual",        False),
("W_REWARD",            10_000.0, "Premio por cubrir turno requerido",                    False),
("W_NOCHE_REWARD",      20_000.0, "Premio extra por cubrir turno nocturno",               False),
("W_NO_PREFERENTE",        500.0, "Penalización si no se asigna turno preferente",        False),
```

**Notas importantes:**
- `W_EXCESO` cambia de `10_000` a `100_000` — esto es intencional y corrige el problema de sobreasignación
- `W_META` cambia de `200_000` a `50_000` — esto es intencional, evita que la meta aplaste la cobertura
- El seed es idempotente: no insertar si ya existe el código

---

## CAMBIO 2 — Builder lee pesos desde BD via ConfigManager

### Archivo a modificar
`app/scheduler/builder.py`

### Qué hacer
Reemplazar las constantes hardcodeadas al inicio del archivo por lecturas de `ConfigManager`.

**ANTES (hardcodeado):**
```python
W_DEFICIT  = 10_000_000
W_EXCESO   =     10_000
W_EQUIDAD  =  1_000_000
W_META     =    200_000
W_REWARD   =     10_000
W_NOCHE_REWARD = 20_000
```

**DESPUÉS (desde BD via ConfigManager):**
```python
# Leer desde BD — ConfigManager.preload() se llama al inicio de build_model()
# Los valores por defecto aquí son solo fallback de emergencia
W_DEFICIT      = None  # se carga en build_model()
W_EXCESO       = None
W_EQUIDAD      = None
W_META         = None
W_REWARD       = None
W_NOCHE_REWARD = None
```

Y al inicio de `build_model()`, justo después de `ConfigManager.preload()`:
```python
ConfigManager.preload()

# Cargar pesos desde BD
W_DEFICIT      = ConfigManager.get_int('W_DEFICIT',      10_000_000)
W_EXCESO       = ConfigManager.get_int('W_EXCESO',          100_000)  # ← 100k no 10k
W_EQUIDAD      = ConfigManager.get_int('W_EQUIDAD',       1_000_000)
W_META         = ConfigManager.get_int('W_META',             50_000)  # ← 50k no 200k
W_REWARD       = ConfigManager.get_int('W_REWARD',           10_000)
W_NOCHE_REWARD = ConfigManager.get_int('W_NOCHE_REWARD',     20_000)
```

**Los siguientes pesos ya leen de ConfigManager — no tocar:**
```python
# Ya están bien:
w_cambio     = ConfigManager.get_int('W_CAMBIO_TURNO', ...)
w_dominante  = ConfigManager.get_int('W_TURNO_DOMINANTE', ...)
w_no_pref    = ConfigManager.get_int('W_NO_PREFERENTE', ...)
```

---

## CAMBIO 3 — Builder pasa turno real a LegalEngine (GAP crítico)

### Archivo a modificar
`app/scheduler/builder.py`

### El problema
En la función `build_model()`, `resumen_legal` se llama con `turno=None`:
```python
# LÍNEA ~239 — INCORRECTO:
res_w = LegalEngine.resumen_legal(w_obj, None, 7)
```

Con `turno=None`, `LegalEngine.dias_efectivos_semana()` cae en el else y usa
el máximo legal (6 días) ignorando la duración real del turno.

Para un turno de 6h: debería ser `floor(42/6)=7` días pero da `6`.
Para un turno de 4h: debería ser `floor(42/4)=10` (limitado a 6 legal) pero da `6`.
El resultado es el mismo pero el cálculo es incorrecto y no refleja
la realidad cuando `permite_horas_extra=True` o con contratos part-time.

### Qué hacer

Paso 1 — En `build_model()`, construir un `MockTurno` representativo
por trabajador basado en `turnos_meta` y `trabajadores_meta`.
Si el trabajador tiene `turnos_permitidos` (solo_turno), usar la duración
de esos turnos. Si no, usar el promedio de todos los turnos.

```python
# Construir mock turno representativo para cada worker
# Agregar este bloque ANTES del loop de HR5-HR9 (línea ~236)
def _get_mock_turno_worker(w, trabajadores_meta, turnos_meta):
    """Retorna MockTurno con la duración representativa para el worker."""
    meta_w      = trabajadores_meta.get(w, {})
    permitidos  = meta_w.get('turnos_permitidos', None)

    if permitidos:
        horas_list = [turnos_meta[t]['horas'] for t in permitidos if t in turnos_meta]
    else:
        horas_list = [v['horas'] for v in turnos_meta.values() if v.get('horas')]

    duracion = round(sum(horas_list) / len(horas_list), 1) if horas_list else 8.0
    return MockTurno({'horas': duracion, 'es_nocturno': False})
```

Paso 2 — Reemplazar todas las llamadas a `resumen_legal(w_obj, None, ...)` por:

```python
# ANTES:
res_w = LegalEngine.resumen_legal(w_obj, None, 7)
res   = LegalEngine.resumen_legal(w_obj, None, len(s_strs))

# DESPUÉS:
mock_turno_w = _get_mock_turno_worker(w, trabajadores_meta, turnos_meta)
res_w = LegalEngine.resumen_legal(w_obj, mock_turno_w, 7)
res   = LegalEngine.resumen_legal(w_obj, mock_turno_w, len(s_strs))
```

Hay exactamente **3 llamadas** a `resumen_legal` en `builder.py`:
- Línea ~239: `res_w = LegalEngine.resumen_legal(w_obj, None, 7)`
- Línea ~245: `res = LegalEngine.resumen_legal(w_obj, None, len(s_strs))`
- Línea ~313: `res_w = LegalEngine.resumen_legal(MockWorker(meta_w), None, 7)`

Reemplazar las 3.

---

## CAMBIO 4 — Eliminar POST_NOCHE del enum y del builder

### Archivos a modificar
1. `app/models/enums.py`
2. `app/scheduler/builder.py`

### En `enums.py`
Eliminar `POST_NOCHE` del enum y del dict `NATURALEZA_POR_TIPO`:

```python
# ANTES:
class RestrictionType(str, Enum):
    EXCLUIR_TURNO     = "excluir_turno"
    SOLO_TURNO        = "solo_turno"
    TURNO_FIJO        = "turno_fijo"
    TURNO_PREFERENTE  = "turno_preferente"
    POST_NOCHE        = "post_noche"      # ← ELIMINAR

NATURALEZA_POR_TIPO = {
    RestrictionType.EXCLUIR_TURNO:    "hard",
    RestrictionType.SOLO_TURNO:       "hard",
    RestrictionType.TURNO_FIJO:       "hard",
    RestrictionType.POST_NOCHE:       "hard",  # ← ELIMINAR
    RestrictionType.TURNO_PREFERENTE: "soft",
}

# DESPUÉS:
class RestrictionType(str, Enum):
    EXCLUIR_TURNO     = "excluir_turno"
    SOLO_TURNO        = "solo_turno"
    TURNO_FIJO        = "turno_fijo"
    TURNO_PREFERENTE  = "turno_preferente"

NATURALEZA_POR_TIPO = {
    RestrictionType.EXCLUIR_TURNO:    "hard",
    RestrictionType.SOLO_TURNO:       "hard",
    RestrictionType.TURNO_FIJO:       "hard",
    RestrictionType.TURNO_PREFERENTE: "soft",
}
```

**Razón:** HR9 en `builder.py` ya aplica esta regla globalmente para todos los
trabajadores. `POST_NOCHE` como restricción manual es redundante y puede
causar conflictos con HR9.

### En `builder.py` — `preparar_restricciones()`
Eliminar el manejo de `POST_NOCHE` (2 lugares):

**Lugar 1 — en `preparar_restricciones()` (~línea 103):**
```python
# ELIMINAR estas líneas:
elif r.tipo == RestrictionType.POST_NOCHE:
    restricciones_hard.append({'w': t.id, 'd': d_str, 'action': 'post_noche'})
```

**Lugar 2 — en `build_model()` HR3 (~línea 220):**
```python
# ELIMINAR estas líneas:
elif action == 'post_noche':
    idx = dias_del_mes.index(d)
    if idx > 0:
        d_ayer = dias_del_mes[idx-1]
        for tn in turnos_nocturnos:
            for td in turnos_diurnos:
                model.AddImplication(x[w, d_ayer, tn], x[w, d, td].Not())
```

**HR9 global (NO tocar) — líneas ~281-285:**
```python
# Este bloque se mantiene exactamente igual:
if turnos_nocturnos and turnos_diurnos:
    for i in range(N - 1):
        d1, d2 = dias_del_mes[i], dias_del_mes[i+1]
        for tn in turnos_nocturnos:
            for td in turnos_diurnos:
                model.AddImplication(x[w, d1, tn], x[w, d2, td].Not())
```

---

## CAMBIO 5 — Eliminar TrabajadorPreferencia y migrar a TrabajadorRestriccionTurno

### Contexto
`TrabajadorPreferencia` (patrón por día de semana) y `TrabajadorRestriccionTurno`
(restricción por rango de fechas) hacen lo mismo. Se unifica en la segunda.
`TrabajadorRestriccionTurno` simula patrón permanente con `fecha_fin = 2099-12-31`.

### Archivos a modificar
1. `app/models/business.py`
2. `app/scheduler/builder.py` — `preparar_restricciones()`
3. `app/controllers/trabajador_bp.py`
4. Nueva migración de BD

### 5a — Migración de datos (SQL a ejecutar PRIMERO)

```sql
-- Paso 1: Migrar datos existentes de TrabajadorPreferencia
-- a TrabajadorRestriccionTurno antes de eliminar la tabla vieja
INSERT INTO trabajador_restriccion_turno
    (trabajador_id, empresa_id, tipo, naturaleza,
     fecha_inicio, fecha_fin, dias_semana, turno_id, activo, creado_en)
SELECT
    p.trabajador_id,
    t.empresa_id,
    CASE p.tipo
        WHEN 'fijo'        THEN 'turno_fijo'
        WHEN 'solo_turno'  THEN 'solo_turno'
        WHEN 'preferencia' THEN 'turno_preferente'
        ELSE 'turno_preferente'
    END,
    CASE p.tipo
        WHEN 'preferencia' THEN 'soft'
        ELSE 'hard'
    END,
    CURRENT_DATE,
    '2099-12-31',
    json_build_array(p.dia_semana),
    (SELECT id FROM turno
     WHERE abreviacion = p.turno
     AND empresa_id = t.empresa_id
     LIMIT 1),
    true,
    NOW()
FROM trabajador_preferencia p
JOIN trabajador t ON t.id = p.trabajador_id
WHERE NOT EXISTS (
    -- No duplicar si ya existe una restricción equivalente
    SELECT 1 FROM trabajador_restriccion_turno r
    WHERE r.trabajador_id = p.trabajador_id
    AND r.dias_semana::text = json_build_array(p.dia_semana)::text
    AND r.fecha_fin = '2099-12-31'
);

-- Paso 2: Verificar que la migración fue correcta antes de continuar
SELECT COUNT(*) FROM trabajador_preferencia;       -- debe dar N
SELECT COUNT(*) FROM trabajador_restriccion_turno; -- debe dar >= N

-- Paso 3: Solo después de verificar, eliminar tabla vieja
-- DROP TABLE trabajador_preferencia;  -- ejecutar manualmente después de verificar
```

### 5b — `business.py`
Eliminar la clase `TrabajadorPreferencia` completa y su relación en `Trabajador`:

```python
# ELIMINAR de Trabajador:
preferencias = db.relationship('TrabajadorPreferencia', backref='trabajador',
                               lazy=True, cascade="all, delete-orphan")

# ELIMINAR clase completa:
class TrabajadorPreferencia(db.Model):
    ...
```

### 5c — `builder.py` — `preparar_restricciones()`
Eliminar el bloque completo "# 2. PREFERENCIAS HISTÓRICAS":

```python
# ELIMINAR este bloque completo (líneas ~64-83):
# 2. PREFERENCIAS HISTÓRICAS
prefs_por_dia = {}
for p in t.preferencias:
    if p.dia_semana not in prefs_por_dia:
        prefs_por_dia[p.dia_semana] = {'fijo': [], 'preferencia': []}
    if p.tipo in ('fijo', 'preferencia'):
        prefs_dia = prefs_por_dia[p.dia_semana]
        if p.tipo not in prefs_dia: prefs_dia[p.tipo] = []
        prefs_dia[p.tipo].append(p.turno)

for dia_str in dias_del_mes:
    if (t.id, dia_str) in bloqueados: continue
    dt = datetime.strptime(dia_str, '%Y-%m-%d').date()
    py_weekday = dt.weekday()
    if py_weekday in prefs_por_dia:
        prefs_dia = prefs_por_dia[py_weekday]
        if prefs_dia.get('fijo'):
            fijos[(t.id, dia_str)] = prefs_dia['fijo'][0]
        elif prefs_dia.get('preferencia'):
            turnos_bloqueados_por_dia[(t.id, dia_str)] = set(prefs_dia['preferencia'])
```

El bloque "# 3. RESTRICCIONES ESPECIALES SGT 2.1" cubre todo esto y más.
No tocar ese bloque.

---

## CAMBIO 6 — Migración Flask-Migrate

Crear una nueva migración que:
1. Elimine la tabla `trabajador_preferencia` (después de ejecutar el SQL del cambio 5a)
2. No modifique ninguna otra tabla

```python
"""
Migración: eliminar_trabajador_preferencia
Descripción: Unifica restricciones en TrabajadorRestriccionTurno.
             Ejecutar DESPUÉS de verificar la migración de datos del Cambio 5a.
"""
def upgrade():
    op.drop_table('trabajador_preferencia')

def downgrade():
    op.create_table('trabajador_preferencia',
        sa.Column('id',            sa.Integer, primary_key=True),
        sa.Column('trabajador_id', sa.Integer,
                  sa.ForeignKey('trabajador.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('dia_semana',    sa.Integer, nullable=False),
        sa.Column('turno',         sa.String(5), nullable=False),
        sa.Column('tipo',          sa.String(20), nullable=False,
                  server_default='preferencia'),
    )
```

---

## ORDEN DE EJECUCIÓN

```
1. Ejecutar seed_parametros_faltantes.py (Cambio 1)
2. Ejecutar SQL de migración de datos (Cambio 5a) y VERIFICAR conteos
3. Aplicar Cambio 2 (pesos desde BD en builder.py)
4. Aplicar Cambio 3 (turno real a LegalEngine)
5. Aplicar Cambio 4 (eliminar POST_NOCHE)
6. Aplicar Cambio 5b y 5c (eliminar TrabajadorPreferencia del modelo y builder)
7. Crear y aplicar migración Flask (Cambio 6)
8. Reiniciar servidor y probar
```

---

## VALIDACIÓN ESPERADA

Después de aplicar todos los cambios, el test de validación es:

**3 trabajadores full-time, 1 solo turno, dotación 1:**
```
Esperado: cada worker trabaja ~10 días (31/3 ≈ 10.3)
         NO todos trabajando 23-26 días
         Déficit = 0 (los 31 días cubiertos)
         Superávit ≈ 0
```

**Worker con turno de 6h vs 8h:**
```
Worker 42h con turno 6h: meta = floor(42/6) = 7 días/semana
Worker 42h con turno 8h: meta = floor(42/8) = 5 días/semana
Los logs del builder deben mostrar max_dias distintos para cada turno
```

**Turno fijo lunes/mié/vie:**
```
Con TrabajadorRestriccionTurno tipo=TURNO_FIJO, dias_semana=[0,2,4]
El builder DEBE respetar esos días
Sin usar TrabajadorPreferencia (eliminada)
```

---

## RESUMEN DE ARCHIVOS A MODIFICAR

| Archivo | Cambio |
|---|---|
| `seed_oficial.py` | Agregar parámetros faltantes + W_* desde BD |
| `app/models/enums.py` | Eliminar POST_NOCHE |
| `app/models/business.py` | Eliminar clase TrabajadorPreferencia + relación en Trabajador |
| `app/scheduler/builder.py` | Pesos desde ConfigManager + turno real a LegalEngine + eliminar POST_NOCHE + eliminar bloque PREFERENCIAS HISTÓRICAS |
| `migrations/versions/` | Nueva migración drop tabla trabajador_preferencia |
| BD (SQL directo) | Migrar datos antes de eliminar tabla |

**Total: 5 archivos Python + 1 SQL + 1 migración**

---

## LO QUE NO SE DEBE TOCAR

```
✗ solver.py
✗ explain.py
✗ conflict.py
✗ legal_engine.py
✗ config_manager.py
✗ planificacion_bp.py
✗ Cualquier template HTML
✗ Cualquier otro blueprint
✗ HR9 global en builder.py (post-noche GLOBAL se mantiene)
✗ TrabajadorRestriccionTurno (no modificar)
✗ TipoAusencia y su lógica
✗ Lógica de ausencias/bloqueados
```

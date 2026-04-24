# Sistema de reglas dinámicas — Plan de implementación

**Estado:** Pendiente
**Prioridad:** Media (el builder funciona con reglas hardcodeadas por ahora)

---

## 1. Contexto y motivación

El builder actualmente tiene las reglas en 3 capas, todas mezcladas en el código fuente:

| Capa | Descripción | Estado actual |
|---|---|---|
| ¿Existe la regla? | Si se aplica o no | Hardcodeado |
| ¿Es HARD o SOFT? | Enforcement | Hardcodeado |
| ¿Con qué parámetros? | Valores numéricos | BD (parcialmente) |

El flujo operativo real es:
```
Super Admin (tú) mantiene el catálogo de reglas legales
El cliente pide una regla especial
Tú se la creas en su empresa
El builder la lee y aplica automáticamente
```

---

## 2. Nivel de parametrización elegido: Nivel B

**Parámetros + enforcement configurable por empresa.**

No se necesita Nivel C (reglas completamente dinámicas) porque la lógica de cada regla sigue siendo código Python — lo que cambia es si se activa, con qué valores y con qué peso.

---

## 3. Dónde viven los parámetros legales

Los parámetros de ley (42h semanales, 2 domingos libres, máx 6 días consecutivos, etc.)
residen en la **tabla `regla` (catálogo maestro)**, no en la empresa.

```
Tabla regla (catálogo — tú lo mantienes):
  min_free_sundays → params_base = {"value": 2}   ← la ley dice 2
  jornada_semanal  → params_base = {"value": 42}  ← la ley dice 42 hoy
  max_consecutivos → params_base = {"value": 6}   ← la ley dice 6

Tabla regla_empresa (por empresa):
  → Sin entrada      → usa params_base del catálogo (la ley)
  → Con params_custom → usa ese valor (override del cliente)
    Ej: empresa pide 3 domingos libres → params_custom = {"value": 3}
```

### Por qué NO en la empresa

Si los parámetros legales estuvieran en la empresa, cuando la ley cambie habría que
actualizar todas las empresas una por una. Con el catálogo centralizado:

```
2028: ley cambia a 40 horas semanales
  → Cambias params_base en UN solo registro de la tabla regla
  → Todas las empresas sin override lo toman automáticamente ✅
```

### Precedencia de parámetros

```
1. params_custom de la empresa      ← máxima prioridad
2. params_base del catálogo (ley)   ← fallback legal
3. default hardcodeado en builder   ← último fallback de emergencia
```

---

## 4. Distinción clave: Legal vs Operacional

```
LEGAL (origen = 'legal'):
  → No se puede desactivar
  → Cliente puede cambiar el parámetro solo dentro de rangos legales
    Ej: min_free_sundays puede subir de 2 a 4, pero nunca bajar a 1
  → La ley puede cambiar a largo plazo → actualizar params_base en catálogo
  → Ejemplos: jornada_semanal, min_free_sundays, max_dias_consecutivos

OPERACIONAL (origen = 'operacional'):
  → Cliente puede activar/desactivar
  → Cliente puede cambiar parámetros libremente
  → Tú la creas a pedido del cliente
  → Ejemplos: equidad semanal, balance noches, distribución de patrones fijos
```

---

## 5. Cambios en modelo de datos

### 5.1 Tabla `regla` — agregar columnas

```python
class Regla(db.Model):
    __tablename__ = 'regla'

    id             = db.Column(db.Integer, primary_key=True)
    codigo         = db.Column(db.String(50), nullable=False, unique=True)
    nombre         = db.Column(db.String(100), nullable=False)
    descripcion    = db.Column(db.String(255))
    familia        = db.Column(db.String(50), nullable=False)   # descanso|jornada|cobertura|calidad
    enforcement    = db.Column(db.String(10), nullable=False)   # 'hard' | 'soft'  ← NUEVO
    origen         = db.Column(db.String(20), nullable=False)   # 'legal' | 'operacional'  ← NUEVO
    params_base    = db.Column(db.JSON)   # {"value": 2, "peso": 100000}
    activo         = db.Column(db.Boolean, default=True)
    creado_en      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Campos nuevos:**
- `enforcement`: si la regla bloquea el modelo (`hard`) o penaliza (`soft`). No configurable por el cliente.
- `origen`: si viene de la ley chilena (`legal`) o es operacional del cliente (`operacional`).

### 5.2 Tabla `regla_empresa` — sin cambios de esquema

La tabla ya tiene `params_custom` y `activo`. Solo agregar validación de negocio:
- Si `regla.origen == 'legal'` → `activo` no puede ser `False`.
- Si `regla.origen == 'legal'` → `params_custom` debe respetar los rangos legales mínimos.

---

## 6. Catálogo completo de reglas a seedear

### Reglas HARD legales (no desactivables, parámetros protegidos)

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `max_turno_por_dia` | Máximo 1 turno por día | jornada | `{}` |
| `jornada_semanal` | Jornada semanal máxima (horas) | jornada | `{"value": 42}` |
| `max_dias_consecutivos` | Máximo días consecutivos | descanso | `{"value": 6}` |
| `min_free_sundays` | Domingos libres mínimos al mes | descanso | `{"value": 2}` |
| `post_turno_nocturno` | Post noche → solo noche o descanso | descanso | `{}` |
| `tope_horas_semanales` | Tope horas semanales proporcional | jornada | `{"duracion_turno": 8}` |
| `total_mensual_contrato` | Total mensual según contrato | jornada | `{"tolerancia": 1}` |

### Reglas HARD operacionales (el cliente puede configurar)

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `dias_descanso_post_6` | Días libres tras 6 trabajados | descanso | `{"value": 1}` |
| `working_days_limit` | Límite días por semana | jornada | `{"min": 5, "max": 6}` |

### Reglas SOFT legales

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `cobertura_minima` | Cobertura mínima por turno y día | cobertura | `{"peso": 10000000}` |

### Reglas SOFT operacionales (el cliente puede activar/desactivar y configurar)

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `exceso_cobertura` | Penalizar exceso de dotación | cobertura | `{"peso": 100000}` |
| `equidad_mensual` | Equidad de carga mensual | calidad | `{"peso": 100000}` |
| `equidad_semanal` | Equidad de carga semanal | calidad | `{"peso": 5000}` |
| `min_dias_semana` | Mínimo días/semana según contrato | jornada | `{"peso": 2000}` |
| `max_dias_semana` | Máximo días/semana según contrato | jornada | `{"peso": 1000}` |
| `anti_fragmentacion` | Penalizar días trabajados aislados | calidad | `{"peso": 100}` |
| `reward_consecutivos` | Recompensar días consecutivos | calidad | `{"peso": 50}` |
| `balance_noches` | Balancear turnos noche equitativamente | calidad | `{"peso": 10}` |
| `reward_utilizacion` | Recompensar utilización del personal | calidad | `{"peso": 1}` |

---

## 7. Cómo el builder leerá las reglas

En `planificacion_bp.py`, antes de llamar al builder, se construye `reglas_activas`
resolviendo la precedencia: params_custom > params_base > default hardcodeado.

```python
# planificacion_bp.py
reglas_activas = {}
reglas_empresa = ReglaEmpresa.query.filter_by(
    empresa_id=empresa_id, activo=True
).join(Regla).filter(Regla.activo == True).all()

for re in reglas_empresa:
    codigo = re.regla_rel.codigo
    # Precedencia: override empresa > ley del catálogo
    params = re.params_custom if re.params_custom else re.regla_rel.params_base
    reglas_activas[codigo] = {
        'enforcement': re.regla_rel.enforcement,
        'origen':      re.regla_rel.origen,
        'params':      params,
    }

model, x = build_model(..., reglas_activas=reglas_activas)
```

En el builder, cada regla se activa condicionalmente:

```python
# Ejemplo: min_free_sundays
r = reglas_activas.get('min_free_sundays')
min_dom = r['params'].get('value', 2) if r else 2   # fallback hardcodeado

if r and r['enforcement'] == 'hard':
    model.Add(domingos_libres >= min_dom)   # HARD: bloquea
else:
    # SOFT: penaliza si no se cumple (peso desde params)
    peso = r['params'].get('peso', 50000) if r else 50000
    ...
```

---

## 8. Validaciones de negocio

### Reglas legales no desactivables

```python
# En regla_empresa bp, al guardar:
if regla.origen == 'legal' and not activo:
    return jsonify({'ok': False,
                    'msg': 'Las reglas legales no pueden desactivarse.'}), 400
```

### Parámetros dentro de rangos legales

```python
RANGOS_LEGALES = {
    'min_free_sundays':      {'min': 2,  'max': None},
    'max_dias_consecutivos': {'min': None, 'max': 6},
    'dias_descanso_post_6':  {'min': 1,  'max': None},
    'jornada_semanal':       {'min': None, 'max': 42},  # 2028: bajar a 40
}
```

---

## 9. Mantenedor UI — pantallas necesarias

### 9.1 Catálogo de reglas (Solo Super Admin)
- Ver todas las reglas del sistema separadas por origen (legal / operacional)
- Editar `params_base` cuando cambia la ley (ej. 2028: jornada_semanal → 40)
- Activar/desactivar reglas del catálogo
- Crear nuevas reglas operacionales a pedido del cliente

### 9.2 Reglas por empresa (Super Admin y Cliente)
- Ver reglas activas de la empresa agrupadas por familia
- Activar reglas operacionales disponibles
- Personalizar `params_custom` dentro de rangos legales permitidos
- Las reglas con `origen = 'legal'` se muestran como no editables en enforcement
- No puede ver ni tocar reglas de otras empresas

---

## 10. Plan de implementación — 3 pasos

### Paso 1 — Migración y seed

```
1a. Agregar columnas enforcement y origen a tabla regla
1b. Seed de todas las reglas del catálogo (sección 6)
1c. Crear regla_empresa para empresas existentes con params por defecto
```

### Paso 2 — Builder lee reglas desde BD

```
2a. Cambiar firma de build_model: reglas_activas en vez de reglas
2b. Cada regla se activa condicionalmente según BD
2c. Pesos SOFT se leen desde params_base/params_custom
2d. Fallback a valores hardcodeados si no hay regla_empresa (retrocompatible)
```

### Paso 3 — Mantenedor UI

```
3a. Catálogo de reglas (Super Admin)
3b. Reglas por empresa con validaciones
3c. Impedir desactivar reglas legales
3d. Validar rangos legales en params_custom
```

---

## 11. Impacto en código existente

Al implementar este sistema, los cambios en `builder.py` son:

- Las constantes `W_DEFICIT`, `W_EXCESO`, etc. se reemplazan por lectura de `params_base.peso`
- Cada bloque de regla se envuelve en `if codigo in reglas_activas`
- La firma cambia de `reglas=dict` a `reglas_activas=dict`
- Los defaults hardcodeados se mantienen como fallback

El cambio es **retrocompatible**: si no hay `ReglaEmpresa` registradas, el builder
funciona igual que hoy.

---

## 12. Cambios legales programados

| Año | Cambio | Campo afectado | Acción |
|---|---|---|---|
| 2026 (hoy) | Jornada máxima 42h (empresas >25 trabajadores) | `jornada_semanal.params_base` | Ya en catálogo |
| 2028 | Jornada máxima 40h (todas las empresas) | `jornada_semanal.params_base` | Actualizar `{"value": 40}` |
| 2028 | Validación legal cambia a 40 | `RANGOS_LEGALES['jornada_semanal']` | Actualizar en código |

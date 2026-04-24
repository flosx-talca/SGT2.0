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

## 3. Distinción clave: Legal vs Operacional

```
LEGAL (origen = 'legal'):
  → No se puede desactivar
  → Cliente puede cambiar el parámetro solo dentro de rangos legales
    Ej: min_free_sundays puede subir de 2 a 4, pero nunca bajar a 1
  → La ley puede cambiar a largo plazo → actualizar params_base en catálogo

OPERACIONAL (origen = 'operacional'):
  → Cliente puede activar/desactivar
  → Cliente puede cambiar parámetros libremente
  → Tú la creas a pedido del cliente
  → Ejemplos: equidad semanal, balance noches, distribución de patrones fijos
```

---

## 4. Cambios en modelo de datos

### 4.1 Tabla `regla` — agregar columnas

```python
class Regla(db.Model):
    __tablename__ = 'regla'

    id           = db.Column(db.Integer, primary_key=True)
    codigo       = db.Column(db.String(50), nullable=False, unique=True)
    nombre       = db.Column(db.String(100), nullable=False)
    descripcion  = db.Column(db.String(255))                          # texto para el admin
    familia      = db.Column(db.String(50), nullable=False)           # descanso|jornada|cobertura|calidad
    enforcement  = db.Column(db.String(10), nullable=False)           # 'hard' | 'soft'  ← NUEVO
    origen       = db.Column(db.String(20), nullable=False)           # 'legal' | 'operacional'  ← NUEVO
    params_base  = db.Column(db.JSON)                                 # {"value": 2, "peso": 100000}
    activo       = db.Column(db.Boolean, default=True)
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Campos nuevos:**
- `enforcement`: indica si la regla bloquea el modelo (`hard`) o penaliza (`soft`). No configurable por el cliente.
- `origen`: indica si la regla viene de la ley chilena (`legal`) o es una regla operacional del cliente (`operacional`).

### 4.2 Tabla `regla_empresa` — sin cambios de esquema

La tabla ya tiene `params_custom` y `activo`. Solo agregar validación de negocio:
- Si `regla.origen == 'legal'` → `activo` no puede ser `False` (validar en el endpoint).
- Si `regla.origen == 'legal'` → `params_custom` debe respetar los rangos legales.

---

## 5. Catálogo completo de reglas a seedear

### Reglas HARD legales (no desactivables)

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `max_turno_por_dia` | Máximo 1 turno por día | jornada | `{}` |
| `max_dias_consecutivos` | Máximo días consecutivos | descanso | `{"value": 6}` |
| `min_free_sundays` | Domingos libres mínimos al mes | descanso | `{"value": 2}` |
| `post_turno_nocturno` | Post noche → solo noche o descanso | descanso | `{}` |
| `tope_horas_semanales` | Tope horas semanales proporcional | jornada | `{"duracion_turno": 8}` |
| `total_mensual_contrato` | Total mensual según contrato | jornada | `{"tolerancia": 1}` |

### Reglas HARD operacionales (configurables)

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `dias_descanso_post_6` | Días libres tras 6 trabajados | descanso | `{"value": 1}` |
| `working_days_limit` | Límite días por semana | jornada | `{"min": 5, "max": 6}` |

### Reglas SOFT legales

| Código | Nombre | Familia | Params base |
|---|---|---|---|
| `cobertura_minima` | Cobertura mínima por turno y día | cobertura | `{"peso": 10000000}` |

### Reglas SOFT operacionales (configurables)

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

## 6. Cómo el builder leerá las reglas

En vez de constantes hardcodeadas al inicio del archivo, el builder recibirá un diccionario de reglas resueltas desde `planificacion_bp.py`:

```python
# planificacion_bp.py — construir reglas_activas antes de llamar al builder
reglas_activas = {}
reglas_empresa = ReglaEmpresa.query.filter_by(
    empresa_id=empresa_id, activo=True
).join(Regla).filter(Regla.activo == True).all()

for re in reglas_empresa:
    codigo = re.regla_rel.codigo
    params = re.params_custom if re.params_custom else re.regla_rel.params_base
    reglas_activas[codigo] = {
        'enforcement': re.regla_rel.enforcement,
        'origen':      re.regla_rel.origen,
        'params':      params,
    }

# Pasar al builder:
model, x = build_model(
    ...,
    reglas_activas=reglas_activas,
)
```

En el builder, cada regla se activa condicionalmente:

```python
# Ejemplo: min_free_sundays
if 'min_free_sundays' in reglas_activas:
    r = reglas_activas['min_free_sundays']
    min_dom = r['params'].get('value', 2)
    if r['enforcement'] == 'hard':
        model.Add(domingos_libres >= min_dom)
    else:
        # soft: penalizar si no se cumple
        ...
```

---

## 7. Validaciones de negocio importantes

### Reglas legales no desactivables

```python
# En regla_empresa bp, al guardar:
if regla.origen == 'legal' and not activo:
    return jsonify({'ok': False,
                    'msg': 'Las reglas legales no pueden desactivarse.'}), 400
```

### Parámetros dentro de rangos legales

```python
# Ejemplo: min_free_sundays no puede ser menor a 2 (ley)
RANGOS_LEGALES = {
    'min_free_sundays':    {'min': 2, 'max': None},
    'max_dias_consecutivos': {'min': None, 'max': 6},
    'dias_descanso_post_6':  {'min': 1, 'max': None},
}
```

---

## 8. Mantenedor UI — pantallas necesarias

### 8.1 Catálogo de reglas (Super Admin)
- Ver todas las reglas del sistema
- Editar `params_base` cuando cambia la ley
- Activar/desactivar reglas del catálogo
- Crear nuevas reglas operacionales

### 8.2 Reglas por empresa (Super Admin / Cliente)
- Ver reglas activas de la empresa
- Activar reglas operacionales disponibles
- Personalizar `params_custom` dentro de rangos permitidos
- No puede ver ni tocar reglas de otras empresas

---

## 9. Plan de implementación — 3 pasos

### Paso 1 — Migración y seed (BD)

```
1a. Agregar columnas enforcement y origen a tabla regla
1b. Seed de todas las reglas del catálogo (ver sección 5)
1c. Crear regla_empresa para empresas existentes con params por defecto
```

### Paso 2 — Builder lee reglas desde BD

```
2a. Cambiar firma de build_model: reglas_activas en vez de reglas
2b. Cada regla se activa condicionalmente según BD
2c. Pesos SOFT se leen desde params_base/params_custom
2d. Fallback a valores hardcodeados si no hay regla_empresa (compatibilidad)
```

### Paso 3 — Mantenedor UI

```
3a. Catálogo de reglas (Super Admin)
3b. Reglas por empresa
3c. Validaciones de negocio (legales no desactivables, rangos)
```

---

## 10. Impacto en código existente

Al implementar este sistema, los cambios en `builder.py` son:

- Las constantes `W_DEFICIT`, `W_EXCESO`, etc. se reemplazan por lectura de `params_base.peso`
- Cada bloque de regla se envuelve en `if codigo in reglas_activas`
- La firma cambia de `reglas=dict` a `reglas_activas=dict`
- Los defaults hardcodeados se mantienen como fallback para no romper entornos sin reglas en BD

El cambio es retrocompatible: si no hay `ReglaEmpresa` registradas, el builder funciona igual que hoy.

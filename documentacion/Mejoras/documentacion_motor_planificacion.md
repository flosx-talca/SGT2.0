# Documentación técnica — Motor de planificación (scheduler)

**Archivos:** `scheduler/builder.py` · `planificacion_bp.py`
**Última actualización:** Abril 2026

---

## 1. Arquitectura del flujo

```
planificacion_bp.py  →  preparar_restricciones()  →  build_model()  →  solve_model()  →  extract_solution()
       │                        │                          │
  Prepara datos            Pre-procesa               Construye modelo
  desde BD              BLOQUEADOS/FIJOS/LIBRE        CP-SAT con
                         antes del solver              todas las reglas
```

El flujo se divide en tres fases:

**Fase 1 — Preparación de datos** (`planificacion_bp.py`): consulta BD, normaliza coberturas, construye metadatos de trabajadores y turnos.

**Fase 2 — Pre-procesamiento** (`preparar_restricciones`): clasifica cada `(trabajador, día)` antes de que el solver intervenga.

**Fase 3 — Optimización** (`build_model` + `solve_model`): construye el modelo CP-SAT y lo resuelve.

---

## 2. Pre-procesamiento: `preparar_restricciones()`

Clasifica cada `(trabajador, día)` en tres categorías con orden estricto de precedencia:

| Categoría | Descripción | Efecto en CP-SAT |
|---|---|---|
| **BLOQUEADO** | Vacaciones, licencia, permiso, compensatorio | `x[w,d,t] = 0` en todos los turnos |
| **FIJO** | Patrón día/turno definido en mantenedor del trabajador | `x[w,d,t_fijo] = 1` como SOFT muy alto |
| **LIBRE** | Sin restricción específica | Solver optimiza |

**Reglas del pre-procesamiento:**

1. BLOQUEADO prevalece sobre todo — ninguna otra regla puede asignar turno en un día bloqueado.
2. FIJO prevalece sobre LIBRE — pero NO prevalece sobre restricciones contractuales (HR5, HR10).
3. Los **domingos nunca reciben patrones FIJO** — los maneja HR7 directamente.
4. Un día bloqueado nunca recibe patrón FIJO aunque exista el patrón para ese día de semana.

**Firma:**
```python
bloqueados, fijos = preparar_restricciones(
    trabajadores_db,   # lista de objetos Trabajador ORM
    dias_del_mes,      # lista de strings 'YYYY-MM-DD'
    ausencias          # dict { (worker_id, fecha): motivo }
)
```

---

## 3. Reglas HARD del modelo (`build_model`)

Las reglas HARD son restricciones absolutas. Si no pueden satisfacerse simultáneamente, el solver retorna `INFEASIBLE`.

### HR1 — Días bloqueados
Vacaciones, licencias, permisos y compensatorios bloquean completamente al trabajador ese día. Máxima precedencia.

```
x[w, d, t] = 0  para todo t en ese día
```

### HR2 — Patrones fijos por día de semana (SOFT-HARD)
Los patrones definidos en el mantenedor del trabajador se aplican con peso `W_ASIG = 1.000.000`. Son tratados como **SOFT muy alto** (no HARD puro) porque pueden entrar en conflicto con HR5 y HR10 para trabajadores part-time o con muchos patrones.

El solver los viola solo cuando las restricciones contractuales o legales lo impiden matemáticamente. En la práctica se respetan en más del 99% de los casos.

```
Ejemplo: Pepito, lunes → turno M (siempre)
→ x[Pepito, lun_1, M] = 1  (viola = 0, penalización = 0)
→ x[Pepito, lun_1, T] = 0
→ x[Pepito, lun_1, I] = 0
→ x[Pepito, lun_1, N] = 0
```

### HR3 — Turnos no permitidos por trabajador
Si `turnos_permitidos` está definido en `trabajadores_meta`, el trabajador solo puede ser asignado a esos turnos.

```
turnos_permitidos = None      → puede hacer cualquier turno
turnos_permitidos = ['M','T'] → solo turno M o T
```

### HR4 — Máximo 1 turno por día
Un trabajador no puede tener más de un turno asignado el mismo día.

### HR5 — Tope horas semanales proporcional
Limita los turnos por semana según las horas contratadas. Usa semanas calendario del mes (ventanas de 7 días desde el día 1).

```
tope_turnos = ceil(horas_semanales * n_dias_semana / 7 / duracion_turno)
```

**Regla crítica sobre horas extra:**

El tope usa `math.ceil()` (no `int()`). Para 42h/8h = 5.25, el tope es **6** (no 5).

`int()` truncaría a 5, lo que causaría `INFEASIBLE` para trabajadores con patrones FIJO de 6 días/semana.

El turno fraccionario (la diferencia entre 5.25 y 6) lo asume el empleador por defecto. Si el trabajador tiene `permite_horas_extra = True`, se permite **1 turno adicional** por semana:

```
42h / 8h = 5.25 → ceil = 6 días (tope normal)
Con permite_horas_extra = True → 7 días (tope con extra)
```

⚠️ **Pendiente implementar:** El campo `permite_horas_extra` en el modelo `Trabajador` no está implementado todavía. Cuando se implemente, el tope semanal cambiará automáticamente.

### HR6 — Máximo días consecutivos
Configurable por trabajador (`max_dias_consecutivos`, default 6). Equivale a la ley de descanso: en cualquier ventana de `max_consec + 1` días, no puede haber más de `max_consec` trabajados.

```
max_dias_consecutivos = 6:
  ventana de 7 días → máximo 6 trabajados → mínimo 1 libre
```

### HR7 — Mínimo domingos libres al mes
Configurable por cliente desde `ReglaEmpresa`. Default: 2 domingos libres.

```
Mes con 4 domingos, min_free_sundays = 2:
  max_dom_trabajo = 4 - 2 = 2 → puede trabajar máximo 2 domingos

Mes con 5 domingos, min_free_sundays = 2:
  max_dom_trabajo = 5 - 2 = 3 → puede trabajar máximo 3 domingos
```

⚠️ **Pendiente revisar — caso del quinto domingo:** En meses con 5 domingos, el solver puede dejar el quinto domingo sin dotación completa porque ya asignó los 3 permitidos a algunos trabajadores y no todos tienen ese domingo disponible. Ver sección de pendientes.

### HR8 — Cobertura mínima por turno y día
Garantiza que haya al menos la dotación requerida en cada turno cada día. La dotación viene del turno (BD) y puede ser sobreescrita por el usuario antes de generar (override en el frontend).

```
sum(x[w, d, t] para w en trabajadores) >= dotacion_requerida[d][t]
```

### HR9 — Post turno nocturno
Tras un turno nocturno, el día siguiente solo puede ser otro turno nocturno o descanso. Se basa en el atributo `es_nocturno` del turno, calculado automáticamente desde `hora_inicio`/`hora_fin` al guardar.

```
hora_fin <= hora_inicio → es_nocturno = True
N (23:00 → 07:00): el día siguiente NO puede ser M, I o T
                   el día siguiente SÍ puede ser N o L
```

### HR10 — Total mensual según contrato
Garantiza que cada trabajador haga los turnos que corresponden a sus horas contratadas en el mes. Usa `math.ceil()` — el empleador asume el turno fraccionario.

```
meta_mensual = ceil(dias_disponibles / 7 * horas_semanales / duracion_turno)
Rango: [meta - 1, meta + 1]
```

El rango ±1 absorbe conflictos matemáticos cuando otras restricciones HARD (domingos libres, días consecutivos, patrones fijos) reducen los días disponibles reales.

---

## 4. Reglas SOFT del modelo — Función objetivo

El solver minimiza una función de costo. Los pesos determinan la jerarquía: violar una regla de mayor peso nunca es compensado por mejorar muchas reglas de menor peso.

| Código | Peso | Descripción |
|---|---|---|
| W_ASIG | 1.000.000 | Patrones FIJO violados (ver HR2) |
| W_DEFICIT | 10.000.000 | Déficit de cobertura — prioridad absoluta |
| W_EXCESO | 100.000 | Exceso de cobertura (sobrepasa la dotación) |
| W_EQUIDAD | 100.000 | Equidad de carga mensual por grupo de contrato |
| W_EQ_SEM | 5.000 | Equidad de carga semanal por grupo de contrato |
| W_MIN_SEM | 2.000 | Mínimo días/semana según contrato |
| W_MAX_SEM | 1.000 | Máximo días/semana según contrato |
| W_FRAG | 100 | Anti-fragmentación (día trabajado aislado) |
| W_CONSEC | 50 | Reward días consecutivos (agrupa días libres) |
| W_NOCHE | 10 | Balancear turnos noche equitativamente |
| W_REWARD | 1 | Utilización del personal disponible |

### SR-DEFICIT — Cobertura mínima (peso 10.000.000)
Penaliza fuertemente cualquier turno que no tenga la dotación requerida. Es la regla de mayor prioridad en el sistema — resolver 1 déficit siempre vale más que resolver cualquier cantidad de reglas menores combinadas.

### SR-EXCESO — Exceso de cobertura (peso 100.000)
Penaliza asignar más personas de las necesarias en un turno. Busca dotación exacta.

### SR-EQUIDAD — Equidad mensual (peso 100.000)
Minimiza la diferencia entre el trabajador que más días trabaja y el que menos, dentro del mismo grupo de horas contratadas. Los grupos de 30h y 42h se evalúan por separado.

### SR-EQ-SEM — Equidad semanal (peso 5.000)
Igual que SR-EQUIDAD pero por semana. Evita que un trabajador trabaje todo al inicio del mes y otro todo al final.

### SR-MIN-SEM / SR-MAX-SEM — Límites semanales (peso 2.000 / 1.000)
Penaliza semanas por debajo del mínimo o por encima del máximo según el contrato.

### SR-FRAG — Anti-fragmentación (peso 100)
Penaliza días trabajados aislados: un día trabajado precedido y seguido de días libres.
```
L T L → penalizado  (día aislado)
T T T → no penalizado
```

### SR-CONSEC — Reward días consecutivos (peso 50)
Recompensa cada par de días adyacentes trabajados. Efecto: el solver agrupa los días libres en bloques en vez de dispersarlos. Especialmente útil para part-time con muchos días libres al mes.

### SR-NOCHE — Balance turnos noche (peso 10)
Penaliza acumular muchos turnos noche en el mismo trabajador. Distribuye las noches equitativamente.

### SR-REWARD — Utilización (peso 1)
Recompensa asignar cuando hay cobertura requerida ese día/turno. Actúa como desempate de último nivel.

---

## 5. `planificacion_bp.py` — Flujo completo

### Datos que entran al endpoint `/planificacion/generar`

```json
{
  "mes": 4,
  "anio": 2026,
  "sucursal_id": 1,
  "cob_M": 1,
  "cob_T": 1,
  "cob_I": 1,
  "cob_N": 1,
  "cob_sun_M": 1,
  "cob_sun_T": 0
}
```

El usuario puede sobreescribir la dotación por turno antes de generar. Si no envía `cob_sun_X`, se usa el valor global del turno.

### Construcción de `trabajadores_meta`

```python
trabajadores_meta = {
    t.id: {
        'horas_semanales': t.horas_semanales or 42,   # default jornada estándar
        'turnos_permitidos': None,                     # pendiente implementar
        'permite_horas_extra': False,                  # pendiente implementar
        'max_dias_consecutivos': 6,                    # pendiente implementar
        'duracion_turno': 8,                           # calculado desde turnos_meta
    }
}
```

### Construcción de `turnos_meta`

```python
def calcular_horas_turno(hora_inicio, hora_fin):
    h_ini = hora_inicio.hour * 60 + hora_inicio.minute
    h_fin = hora_fin.hour   * 60 + hora_fin.minute
    if h_fin <= h_ini:
        h_fin += 24 * 60
    return (h_fin - h_ini) / 60

turnos_meta = {
    t.abreviacion: {
        'es_nocturno': t.es_nocturno,                     # campo en BD
        'horas': calcular_horas_turno(t.hora_inicio, t.hora_fin),
    }
}
```

### Respuesta del endpoint

```json
{
  "status": "ok",
  "data": {
    "dias": [...],
    "trabajadores": [...],
    "celdas": {
      "2026-04-01": {
        "1": "M",   // turno asignado
        "2": "L",   // libre
        "3": "VAC", // vacaciones
        "4": ""     // sin resolver (INFEASIBLE parcial)
      }
    },
    "turnos": [...],
    "estado": "simulacion",
    "advertencia": null,
    "metricas": { "necesarios": 120 }
  }
}
```

**Valores posibles en `celdas[fecha][worker_id]`:**

| Valor | Significado |
|---|---|
| `"M"`, `"T"`, `"N"`, etc. | Turno asignado por el solver |
| `"L"` | Libre — el solver asignó descanso |
| `"VAC"`, `"LM"`, etc. | Ausencia registrada (abreviación del tipo) |
| `""` | Sin resolver — INFEASIBLE, el usuario completa manualmente |

---

## 6. Atributos necesarios en BD

### Turno
| Campo | Tipo | Descripción |
|---|---|---|
| `hora_inicio` | `Time(timezone=False)` | Hora de inicio del turno |
| `hora_fin` | `Time(timezone=False)` | Hora de fin del turno |
| `es_nocturno` | `Boolean` | Calculado al guardar: `hora_fin <= hora_inicio` |
| `dotacion_diaria` | `Integer` | Dotación base (override posible al generar) |

### Trabajador
| Campo | Tipo | Descripción |
|---|---|---|
| `horas_semanales` | `Integer NOT NULL DEFAULT 42` | Horas contractuales por semana |

### ReglaEmpresa (codigos relevantes)
| Código | Params | Descripción |
|---|---|---|
| `working_days_limit` | `{"min": 5, "max": 6}` | Límite días por semana |
| `min_free_sundays` | `{"value": 2}` | Domingos libres mínimos |
| `dias_descanso_post_6` | `{"value": 1}` | Días libres tras 6 trabajados |
| `jornada_semanal` | `{"value": 42}` | Jornada default si el trabajador no tiene horas |
| `duracion_turno` | `{"value": 8}` | Duración estándar del turno en horas |

---

## 7. Bugs conocidos corregidos durante desarrollo

| Bug | Descripción | Fix |
|---|---|---|
| `int()` en HR5 | `int(5.25) = 5` limitaba a 5 días causando INFEASIBLE con patrones de 6 días | `math.ceil(5.25) = 6` |
| Anti-fragmentación inactiva | `OnlyEnforceIf` unidireccional → solver siempre elegía `pen=0` | Restricción bidireccional |
| Anti-fragmentación errónea | Penalizaba fin de bloque, no día aislado | Ventana de 3 días: ayer/hoy/mañana |
| Límites semanales hardcodeados | Umbrales mágicos `horas <= 30` → 30h part-time no recibía límite correcto | Calculado desde `horas/duracion` |
| Equidad mezcla contratos | Comparaba full-time con part-time (diferencia estructural ~8 días) | Agrupado por `horas_semanales` |
| Patrones fijos HARD | HR2 como HARD + HR5 causaban INFEASIBLE para part-time con muchos patrones | HR2 como SOFT con `W_ASIG = 1.000.000` |
| Domingos en patrones | Patrones del domingo + HR7 (min domingos libres) → INFEASIBLE | Domingos excluidos de `preparar_restricciones` |
| Cobertura fallback frágil | `coberturas.get(d, coberturas)` fallaba con formato mixto | Normalización al inicio |

---

## 8. Pendientes de implementación

### P1 — Horas extra por trabajador (campo `permite_horas_extra`)

**Estado:** Definido en documentación, no implementado en BD ni en código.

**Descripción:** El tope semanal HR5 usa `math.ceil(horas/duracion)` que incluye automáticamente el turno fraccionario. El turno extra adicional (más allá del ceil) debe ser opt-in por trabajador.

**Comportamiento esperado:**
```
42h / 8h = 5.25 → ceil = 6 días (tope normal, empleador paga fracción)
Con permite_horas_extra = True → 7 días (turno extra voluntario)
Sin permite_horas_extra = False → 6 días (máximo)
```

**Cambios necesarios:**
- Agregar `permite_horas_extra = Boolean DEFAULT FALSE` al modelo `Trabajador`
- Migración de BD
- Exponer en mantenedor de trabajadores
- El builder ya tiene el código listo (`if extra_ok: tope_turnos += 1`)

---

### P2 — Quinto domingo sin dotación completa

**Estado:** Caso detectado en producción, no resuelto.

**Descripción:** En meses con 5 domingos, HR7 permite trabajar hasta 3 domingos. Si algunos trabajadores ya tienen 3 domingos trabajados asignados pero hay más domingos disponibles en el mes, el quinto domingo puede quedar sin dotación completa.

**Causa raíz:** HR7 limita *cuántos domingos trabaja cada trabajador*, pero no garantiza que *todos los domingos tengan dotación mínima*. HR8 (cobertura mínima) puede quedar insatisfecha en el quinto domingo si no hay trabajadores disponibles que aún puedan trabajar ese día.

**Alternativas a evaluar:**
1. Reducir la dotación requerida para el quinto domingo (cobertura especial domingos extras).
2. Permitir que HR7 sea flexible: si ya hay 2 libres, el tercero es el mínimo pero puede trabajar el quinto si la operación lo requiere.
3. Pre-asignar el quinto domingo en `planificacion_bp.py` rotando trabajadores que tengan menos domingos trabajados ese mes.

---

### P3 — Turnos permitidos por trabajador

**Estado:** Campo `turnos_permitidos` definido en documentación, no completamente integrado.

**Descripción:** Permite restringir a un trabajador para que solo pueda ser asignado a ciertos turnos (ej. solo turno noche).

**Cambios necesarios:**
- Verificar que `turnos_permitidos` llega correctamente en `trabajadores_meta` desde `planificacion_bp.py`
- Exponer en mantenedor de trabajadores

---

### P4 — Parametrizar pesos de la función objetivo en BD

**Estado:** Pesos hardcodeados como constantes al inicio de `builder.py`.

**Descripción:** Cada cliente podría calibrar la importancia relativa de las reglas SOFT según su operación. Un cliente podría priorizar equidad sobre cobertura exacta, otro al revés.

**Cambios necesarios:**
- Agregar códigos de regla para cada peso en tabla `Regla`
- Leer los pesos desde `ReglaEmpresa` al inicio de `build_model`
- Mantener los valores hardcodeados como fallback

---

### P5 — Compensatorios como días bloqueados en siguiente planificación

**Estado:** Modelo `Compensatorio` definido en documentación, no integrado con `preparar_restricciones`.

**Descripción:** Los compensatorios pendientes (domingos y feriados trabajados) deben aparecer como días BLOQUEADOS en la planificación del mes siguiente cuando el administrador asigne fecha de compensatorio.

# PROMPT PARA CURSOR / ANTIGRAVITY — CORRECCIONES MOTOR SGT 2.1

> Pega este prompt en el chat del IDE con el archivo de contexto
> `contexto_motor_cuadrante_v2.md` adjunto como referencia.
> Aplica los cambios **en el orden indicado**. No implementes el siguiente
> paso sin confirmar el anterior con el usuario.

---

## CONTEXTO

Estoy trabajando en el sistema SGT 2.1, un motor de generación de cuadrantes
de turnos construido con OR-Tools CP-SAT (Python). Adjunto el archivo
`contexto_motor_cuadrante_v2.md` con la documentación técnica completa
del motor, incluyendo arquitectura, jerarquía de restricciones y parámetros.

Se han identificado incongruencias legales respecto al Código del Trabajo
chileno (Art. 38) que deben corregirse. Las correcciones están priorizadas.

**REGLA GENERAL**: No modifiques ningún archivo sin mostrarme el diff primero
y esperar mi aprobación explícita.

---

## PASO 1 — Corregir criterio HR7 en `legal_engine.py`

**Archivo**: `app/services/legal_engine.py`

**Problema**: El método que determina si un trabajador está afecto a los
2 domingos libres obligatorios usa `horas_semanales >= 30` como criterio.
Ese valor es incorrecto. El Art. 38 inciso 4° CT establece que la excepción
aplica a trabajadores con jornada "no superior a veinte horas semanales".

**Cambio requerido**:

```python
# ANTES (incorrecto):
aplica_domingo = trabajador.horas_semanales >= 30

# DESPUÉS (correcto, Art. 38 inc. 4 CT):
def aplica_domingo_obligatorio(trabajador) -> bool:
    return (
        trabajador.empresa.regimen_exceptuado       # Art. 38 N°2 o N°7
        and trabajador.horas_semanales > 20         # jornada > 20h (no >= 30)
        and not getattr(trabajador, "contrato_exclusivo_fds", False)
        and getattr(trabajador, "plazo_contrato_dias", 999) > 30
    )
```

**Impacto esperado**: Trabajadores con jornadas de 21h a 29h/sem que hoy
quedan exentos ilegalmente de HR7 pasarán a tener 2 domingos libres/mes.

**Acción**: Muéstrame el método actual completo de `resumen_legal()` en
`legal_engine.py` y propón el diff con la corrección.

---

## PASO 2 — Actualizar el parámetro en BD y config_manager

**Archivo**: `app/services/config_manager.py` + seed de BD

**Problema**: El parámetro `UMBRAL_DIAS_DOMINGO_OBLIGATORIO` (valor actual = 5.0)
tiene una descripción ambigua o un nombre que confunde. Debe ser reemplazado por
`UMBRAL_HRS_DOMINGO_OBLIGATORIO` con valor 20.0 y descripción clara.

**Cambio requerido en el seed de BD**:

```sql
UPDATE parametro_legal
SET codigo       = 'UMBRAL_HRS_DOMINGO_OBLIGATORIO',
    valor        = 20.0,
    descripcion  = 'Jornada mínima (horas/semana) para que apliquen los 2 domingos libres obligatorios/mes. HR7 activa si horas_semanales > este_valor. Valor legal = 20 (Art. 38 inc. 4 CT). NO modificar sin visación.',
    categoria    = 'domingos'
WHERE codigo = 'UMBRAL_DIAS_DOMINGO_OBLIGATORIO';
```

**Acción**: Muéstrame dónde se usa `UMBRAL_DIAS_DOMINGO_OBLIGATORIO` en
`config_manager.py` y `builder.py` y propón el diff para actualizar la referencia
al nuevo nombre `UMBRAL_HRS_DOMINGO_OBLIGATORIO`.

---

## PASO 3 — Corregir HR7 en `builder.py`

**Archivo**: `app/scheduler/builder.py`

**Problema**: La restricción HR7 usa el resultado de `resumen_legal()` para
determinar `aplica_domingo`. Después del Paso 1, el valor ya vendrá correcto.
Sin embargo, la lógica de conteo de domingos disponibles no descuenta los
domingos con ausencia registrada (bloqueados por HR1).

**Cambio requerido**:

```python
# ANTES: cuenta todos los domingos del mes
domingos_mes = [d for d in dias if d.weekday() == 6]
domingos_libres = sum(1 - sum(x[w,d,t] for t in turnos) for d in domingos_mes)
model.Add(domingos_libres >= 2)

# DESPUÉS: descuenta domingos con ausencia (no cuentan como "otorgados")
domingos_mes = [d for d in dias if d.weekday() == 6]
domingos_disponibles = [
    d for d in domingos_mes
    if (w_id, d.strftime("%Y-%m-%d")) not in bloqueados
]
domingos_libres = sum(
    1 - sum(x[w_id, d, t_id] for t_id in turnos_ids)
    for d in domingos_disponibles
)
model.Add(domingos_libres >= res['min_domingos_mes'])
```

**Acción**: Muéstrame el bloque HR7 actual en `builder.py` y propón el diff.

---

## PASO 4 — Agregar HR11: máximo domingos consecutivos

**Archivo**: `app/scheduler/builder.py`

**Problema**: No existe ninguna restricción que limite los domingos consecutivos
trabajados. El Art. 38 inciso 5° CT establece que no se pueden prestar servicios
por más de 3 domingos en forma consecutiva.

**Cambio requerido** (agregar después del bloque HR7):

```python
# [HR11] Máximo 3 domingos consecutivos trabajados (Art. 38 inc. 5 CT)
domingos_todos = sorted([d for d in dias if d.weekday() == 6])
max_dom_consecutivos = int(config.get("MAX_DOMINGOS_CONSECUTIVOS", 3))

for w_obj in trabajadores:
    if not res_legal[w_obj.id].get('aplica_domingo', False):
        continue  # solo aplica a trabajadores con HR7 activo
    for i in range(len(domingos_todos) - max_dom_consecutivos):
        ventana = domingos_todos[i:i + max_dom_consecutivos + 1]
        model.Add(
            sum(
                sum(x[w_obj.id, d, t.id] for t in turnos_disponibles(w_obj, d))
                for d in ventana
            ) <= max_dom_consecutivos
        )
```

**Acción**: Muéstrame cómo están organizadas las restricciones HR en `builder.py`
(bloques, comentarios, orden) y propón dónde insertar HR11 sin romper el flujo.

---

## PASO 5 — Agregar pre-validación dominical en `scheduling_service.py`

**Archivo**: `app/services/scheduling_service.py`

**Problema**: No existe validación previa que detecte si un trabajador afecto a HR7
tendrá domingos disponibles suficientes considerando sus ausencias del mes.
Si esto no se detecta antes del Solver, el resultado es INFEASIBLE silencioso.

**Cambio requerido** (ejecutar antes de llamar a `build_model()`):

```python
def validar_domingos_factibles(trabajadores, dias, bloqueados, coberturas, config):
    alertas = []
    min_libres = int(config.get("MIN_DOMINGOS_LIBRES_MES", 2))
    domingos_mes = [d for d in dias if d.weekday() == 6]

    for w in trabajadores:
        if not aplica_domingo_obligatorio(w):
            continue

        dom_disponibles = [
            d for d in domingos_mes
            if (w.id, d.strftime("%Y-%m-%d")) not in bloqueados
        ]
        max_trabajables = max(0, len(dom_disponibles) - min_libres)

        # Verificar si se necesita al menos 1 domingo trabajado de este trabajador
        dom_con_demanda = [
            d for d in dom_disponibles
            if sum(coberturas.get(d, {}).values()) > 0
        ]

        if max_trabajables == 0 and len(dom_con_demanda) > 0:
            alertas.append({
                "nivel": "CRITICO",
                "trabajador_id": w.id,
                "nombre": w.nombre,
                "mensaje": (
                    f"Solo tiene {len(dom_disponibles)} domingos disponibles "
                    f"(debe librar {min_libres}). No puede cubrir ningún domingo. "
                    f"Revisar ausencias o reasignar dotación dominical."
                )
            })
    return alertas
```

**Acción**: Muéstrame el método `run_generation()` en `scheduling_service.py`
y propón dónde insertar esta validación y cómo retornar las alertas al controller.

---

## PASO 6 — Actualizar comentarios en `builder.py` (cosmético)

**Archivo**: `app/scheduler/builder.py`

Buscar y reemplazar todas las referencias a:
- `"si jornada >= 30h"` → `"si jornada > 20h (Art. 38 inc. 4 CT)"`
- `"horas >= 30"` → `"horas > 20 y régimen exceptuado"`
- `"UMBRAL_DIAS_DOMINGO_OBLIGATORIO"` → `"UMBRAL_HRS_DOMINGO_OBLIGATORIO"`

**Acción**: Busca todas las ocurrencias de estas cadenas en `builder.py`
y muéstrame el diff de los comentarios afectados.

---

## ORDEN DE APROBACIÓN

Implementar en este orden estricto y esperar confirmación entre pasos:

1. ✅ Paso 1 → corrección criterio (legal_engine.py)
2. ✅ Paso 2 → corrección parámetro (config_manager + seed BD)
3. ✅ Paso 3 → corrección conteo domingos (builder.py)
4. ✅ Paso 4 → nueva restricción HR11 (builder.py)
5. ✅ Paso 5 → pre-validación dominical (scheduling_service.py)
6. ✅ Paso 6 → comentarios (builder.py)

Después de cada paso, ejecutar los tests existentes en `tests/scheduler/`
y confirmar que no hay regresiones antes de continuar.

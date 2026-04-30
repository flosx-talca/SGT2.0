# INCONGRUENCIAS LEGALES — Motor de Cuadrantes SGT 2.1

> **Fecha de revisión**: Abril 2026
> **Base legal**: Código del Trabajo Chile, Art. 38 y Art. 38 bis
> **Autor de la revisión**: Revisión manual vs. texto oficial DT Chile
>
> Este documento debe ser adjuntado al ticket de corrección y archivado
> junto al historial de cambios del motor.

---

## RESUMEN EJECUTIVO

La revisión del documento `contexto_motor_cuadrante.md` contra el texto oficial
del Art. 38 del Código del Trabajo chileno y los dictámenes de la Dirección del
Trabajo identificó **3 incongruencias** y **1 punto no cubierto**:

| # | Tipo | Severidad | Archivo afectado |
|---|---|---|---|
| INC-01 | Criterio legal incorrecto | 🔴 Crítica | `legal_engine.py`, `builder.py` |
| INC-02 | Restricción no implementada | 🔴 Crítica | `builder.py` |
| INC-03 | Obligación legal no documentada | 🟠 Media | Documentación + módulo compensaciones |
| INC-04 | Punto no cubierto | 🟠 Media | `builder.py`, `scheduling_service.py` |

---

## INC-01 — Criterio de activación HR7 incorrecto

### Descripción

El motor y la documentación utilizan `horas_semanales >= 30` para determinar si un
trabajador está afecto a los 2 domingos libres obligatorios por mes (HR7).

Este criterio **no tiene base en el Código del Trabajo** y genera dos tipos de errores:

- **Error tipo I (perjudica al trabajador)**: Trabajadores con jornada entre 21h y 29h/sem
  en régimen exceptuado quedan erróneamente exentos de HR7, privándolos de un derecho legal.
- **Error tipo II (no aplica cuando corresponde)**: Un trabajador de jornada completa (42h)
  en una empresa NO exceptuada recibe el tratamiento de HR7 cuando legalmente no le corresponde
  (porque la empresa no está en régimen exceptuado).

### Texto legal

Art. 38 inciso 4° CT:

> *"al menos dos de los días de descanso en el respectivo mes calendario deberán
> necesariamente otorgarse en día domingo. Esta norma no se aplicará respecto de los
> trabajadores cuya jornada ordinaria no sea superior a veinte horas semanales o se
> contraten exclusivamente para trabajar los días sábado, domingo o festivos."*

### Criterio correcto

Los **dos requisitos copulativos** para que HR7 aplique son:

1. La empresa está en **régimen exceptuado** (Art. 38 N°2 o N°7 CT)
2. La jornada ordinaria del trabajador es **superior a 20 horas semanales**

Excepciones adicionales (HR7 NO aplica aunque se cumplan los requisitos):
- Contrato por plazo de 30 días o menos
- Contratado exclusivamente para trabajar sábado, domingo o festivos

### Corrección requerida

```python
# legal_engine.py

# INCORRECTO (versión actual):
aplica_domingo = trabajador.horas_semanales >= 30

# CORRECTO (Art. 38 inc. 4 CT):
aplica_domingo = (
    trabajador.empresa.regimen_exceptuado
    and trabajador.horas_semanales > 20
    and not trabajador.contrato_exclusivo_fds
    and trabajador.plazo_contrato_dias > 30
)
```

### Impacto en casos concretos

| Trabajador | Horas | Criterio anterior | Criterio correcto | Error |
|---|---|---|---|---|
| Part-time 25h, retail | 25h | ❌ Exento (25 < 30) | ✅ Afecto (25 > 20) | **Privación de derecho** |
| Part-time 28h, hotel | 28h | ❌ Exento (28 < 30) | ✅ Afecto (28 > 20) | **Privación de derecho** |
| Part-time 20h, retail | 20h | ❌ Exento (20 < 30) | ❌ Exento (20 no > 20) | ✅ Correcto por coincidencia |
| Full-time 42h, retail | 42h | ✅ Afecto (42 >= 30) | ✅ Afecto (42 > 20 + excep.) | ✅ Correcto por coincidencia |
| Full-time 42h, oficina | 42h | ✅ Afecto (42 >= 30) | ❌ Exento (no régimen excep.) | **HR7 aplicada sin fundamento** |

---

## INC-02 — Restricción HR11 no implementada (domingos consecutivos)

### Descripción

El Art. 38 inciso 5° CT establece una limitación explícita sobre domingos
consecutivos trabajados que **no existe en ninguna forma en el motor actual**.

### Texto legal

> *"La distribución de los días domingos no podrá considerar la prestación de servicios
> por más de tres domingos en forma consecutiva."*

### Consecuencia

Un trabajador en régimen exceptuado podría ser asignado a trabajar 4, 5 o incluso
todos los domingos del mes en secuencia, sin que el Solver lo detecte como una
infracción. Esto genera un **cuadrante ilegal** que puede derivar en multa de la DT.

### Corrección requerida

Agregar restricción HR11 en `builder.py`:

```python
# [HR11] Máximo 3 domingos consecutivos trabajados (Art. 38 inc. 5 CT)
domingos_todos = sorted([d for d in dias if d.weekday() == 6])
for i in range(len(domingos_todos) - 3):
    ventana = domingos_todos[i:i+4]
    model.Add(
        sum(
            sum(x[w.id, d, t.id] for t in turnos)
            for d in ventana
        ) <= 3
    )
```

---

## INC-03 — Descanso compensatorio no documentado ni implementado

### Descripción

El Art. 38 establece **dos obligaciones distintas** que el documento y el motor
no diferencian correctamente:

| Obligación | Descripción | Estado en el motor |
|---|---|---|
| 2 domingos libres/mes | HR7: al menos 2 domingos del mes sin trabajar | ✅ Implementado (con criterio incorrecto, ver INC-01) |
| Descanso compensatorio | Por cada domingo trabajado, 1 día libre en la semana | ⚠️ Solo tiene parámetros, sin implementación |

Los parámetros `COMP_PLAZO_DIAS_GENERAL = 15` y `COMP_PLAZO_DIAS_EXCEPTUADO = 30`
existen en la BD pero **no están siendo usados por ningún módulo**. Son parámetros
huérfanos sin implementación.

### Texto legal

Art. 38 inciso 3° CT:

> *"Los trabajadores del comercio y de los servicios que atiendan directamente al
> público gozarán de un día de descanso compensatorio por cada día domingo o festivo
> en que deban prestar servicios."*

### Consecuencia

El cuadrante generado puede ser operativamente correcto (cubre turnos, respeta horas)
pero la empresa no tiene un mecanismo automático para rastrear y otorgar los días
compensatorios adeudados por domingos trabajados.

### Corrección requerida

1. Documentar claramente la distinción en `contexto_motor_cuadrante_v2.md` (ya incluido).
2. Crear módulo `compensaciones_service.py` que, post-generación del cuadrante,
   calcule los días compensatorios generados por trabajador y los registre para
   seguimiento del administrador.
3. Los parámetros `COMP_PLAZO_DIAS_*` deben ser usados por ese módulo para alertar
   cuando un día compensatorio está próximo a vencer.

---

## INC-04 — Punto no cubierto: flujo para trabajadores afectos a HR7

### Descripción

El documento anterior describía HR7 como una restricción dura, pero **no documentaba
cómo funciona internamente** cuando el trabajador está afecto. Específicamente,
faltaba documentar:

1. **Cómo se cuentan los domingos**: El Solver debe contar los domingos del mes
   calendario y descontar los que tienen ausencia registrada.

2. **Qué pasa con ausencias en domingo**: Los domingos bloqueados por HR1 (ausencia)
   no deben contar como "domingos libres otorgados". La jurisprudencia de la DT
   (JLT Valdivia, I-23-2016) indica que las ausencias reducen el conteo de domingos
   disponibles, no los reemplazan.

3. **Cuándo se genera INFEASIBLE silencioso**: Si tras descontar ausencias quedan
   menos de 2 domingos disponibles y hay demanda de cobertura dominical, el Solver
   retorna INFEASIBLE sin indicar la causa real.

4. **Pre-validación faltante**: No existía ningún mecanismo para detectar este
   conflicto antes de lanzar el Solver.

### Corrección requerida

Agregar en `scheduling_service.py` la función `validar_domingos_factibles()` que
cruce ausencias dominicales con la dotación requerida y alerte al Admin antes de
ejecutar el Solver (ver Paso 5 del prompt para Cursor).

---

## TABLA CONSOLIDADA DE CORRECCIONES

| ID | Archivo | Línea/Método | Cambio | Prioridad |
|---|---|---|---|---|
| INC-01a | `legal_engine.py` | `resumen_legal()` → campo `aplica_domingo` | Cambiar criterio `>= 30` por `> 20 AND regimen_exceptuado` | 🔴 Crítica |
| INC-01b | `builder.py` | bloque HR7, comentarios | Actualizar texto de comentarios | 🟡 Baja |
| INC-01c | `config_manager.py` | parámetro `UMBRAL_DIAS_DOMINGO_OBLIGATORIO` | Renombrar a `UMBRAL_HRS_DOMINGO_OBLIGATORIO`, valor 20.0 | 🟠 Media |
| INC-01d | seed BD | tabla `parametro_legal` | UPDATE del registro correspondiente | 🟠 Media |
| INC-02 | `builder.py` | después del bloque HR7 | Agregar HR11 (max 3 domingos consecutivos) | 🔴 Crítica |
| INC-03a | documentación | sección 5 del .md | Documentar distinción dom. libres vs. compensatorio | ✅ Ya corregido en v2 |
| INC-03b | nuevo archivo | `compensaciones_service.py` | Crear módulo de seguimiento compensatorio | 🟠 Media |
| INC-04a | `builder.py` | bloque HR7 | Descontar ausencias del conteo de domingos disponibles | 🔴 Crítica |
| INC-04b | `scheduling_service.py` | `run_generation()` | Agregar `validar_domingos_factibles()` pre-Solver | 🔴 Crítica |

---

## CRITERIO DE ACEPTACIÓN

Una vez aplicadas las correcciones, los siguientes tests deben pasar:

```
[TEST-01] Trabajador part-time 25h, régimen exceptuado
          → aplica_domingo_obligatorio() == True

[TEST-02] Trabajador part-time 20h, régimen exceptuado
          → aplica_domingo_obligatorio() == False

[TEST-03] Trabajador full-time 42h, empresa NO exceptuada
          → aplica_domingo_obligatorio() == False

[TEST-04] Mes con 4 domingos, 1 ausencia, trabajador afecto a HR7
          → max_domingos_trabajables == 1 (no 2)

[TEST-05] Trabajador asignado 3 domingos consecutivos
          → válido (HR11 no lo bloquea)

[TEST-06] Trabajador asignado 4 domingos consecutivos
          → INFEASIBLE (HR11 lo bloquea)

[TEST-07] Trabajador afecto a HR7, 0 domingos disponibles, demanda > 0
          → pre-validación retorna alerta CRITICO antes del Solver
```

---

> **Visación requerida**: Toda implementación derivada de este documento debe ser
> revisada y aprobada por el usuario responsable del proyecto antes de ser
> confirmada en el repositorio.

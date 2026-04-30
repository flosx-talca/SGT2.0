# CONTEXTO TÉCNICO: MOTOR DE GENERACIÓN DE CUADRANTES — SGT 2.1

> [!CAUTION]
> **ADVERTENCIA CRÍTICA**: Cualquier modificación al motor de planificación,
> parámetros legales o jerarquía de restricciones **DEBE ser visada y aprobada**
> por el usuario responsable del proyecto antes de ser implementada.
> Esta advertencia aplica a todos los archivos listados en este documento.

---

## 1. PROPÓSITO DEL DOCUMENTO

Este archivo es el **contexto persistente** del módulo de generación de cuadrantes del sistema SGT 2.1.
Está diseñado para ser usado por:

- **IDE (Cursor / Windsurf / Antigravity)**: Como contexto de referencia al editar cualquier archivo relacionado con el motor.
- **Desarrolladores**: Como guía técnica interna del comportamiento del Solver, sus restricciones y prioridades.
- **Responsable del Proyecto**: Como documento de auditoría para visación de cambios.

**Alcance**: Cubre desde la solicitud de generación de cuadrante hasta la entrega del resultado final, incluyendo reglas legales, restricciones individuales, parámetros de optimización y casos borde documentados.

---

## 2. ARCHIVOS QUE INTERVIENEN

| Archivo | Rol |
|---|---|
| `app/scheduler/builder.py` | **Motor principal**. Construye el modelo CP-SAT con OR-Tools. Define variables `x[w,d,t]`, aplica todas las restricciones y ejecuta la optimización. |
| `app/services/scheduling_service.py` | **Orquestador**. Extrae datos desde la BD, prepara metadatos de trabajadores/turnos, llama a `build_model()` y devuelve las asignaciones. |
| `app/services/config_manager.py` | **Gestor de parámetros**. Carga los 43 parámetros legales desde `parametro_legal` en BD y los entrega al motor como caché en memoria. |
| `app/services/legal_engine.py` | **Motor legal**. Calcula `resumen_legal()` por trabajador: horas máximas, días máximos, domingos libres obligatorios según tipo de contrato y régimen. |
| `app/models/business.py` | **Modelos de datos**. Define `Trabajador`, `Turno`, `TrabajadorAusencia`, `TrabajadorRestriccionTurno`, `ReglaEmpresa`. |
| `app/models/enums.py` | **Tipos de restricción**. Define `RestrictionType` y `TipoContrato`. |
| `app/models/core.py` | **Geografía y feriados**. Define `Region`, `Comuna`, `Feriado`. Los feriados impactan los descansos legales del solver. |
| `app/controllers/trabajador_bp.py` | **Mantenedor trabajador**. Gestiona el guardado de ausencias y restricciones individuales de turno. |
| `app/controllers/main_bp.py` | **Endpoint de generación**. Recibe la solicitud HTTP, llama a `SchedulingService.run_generation()` y devuelve el resultado. |
| `app/templates/main/planificacion.html` | **Interfaz de usuario**. Formulario para seleccionar mes/año/sucursal y disparar la generación. Visualiza el cuadrante resultante. |

> Si para profundizar en algún comportamiento es necesario conectarse a la BD PostgreSQL,
> consultar directamente las tablas: `parametro_legal`, `trabajadores`, `turnos`,
> `trabajador_restriccion_turno`, `trabajador_ausencia` y `regla_empresa`.

---

## 3. ARQUITECTURA GENERAL DEL PROCESO

```
[Usuario] → planificacion.html
    │
    ▼
[main_bp.py] → POST /planificacion/generar
    │
    ▼
[SchedulingService.run_generation(mes, anio, sucursal_id)]
    │
    ├─► ConfigManager.preload()            → Carga 43 parámetros desde BD
    ├─► Trabajador.query(sucursal, activo) → Trabajadores activos
    ├─► Turno.query(sucursal, activo)      → Turnos configurados
    ├─► TrabajadorAusencia.query()         → Ausencias del período
    │   └─► bloqueados[(w_id, fecha)]
    ├─► TrabajadorRestriccionTurno.query() → Restricciones individuales
    │   └─► fijos / r_hard / r_soft
    └─► coberturas = {fecha: {turno: dotacion}}
            │
            ▼
        build_model(trabajadores, dias, turnos, coberturas, ...)
            │
            ├─► Variables: x[w, d, t] ∈ {0, 1}
            ├─► [HR1]  Bloqueados por ausencia  → x = 0
            ├─► [HR2]  Turno Fijo               → Hard tipo + Soft presencia
            ├─► [HR2b] Solo este Turno           → permitidos[w,d] = {t}
            ├─► [HR3]  Excluir Turno             → x[w,d,t_excl] = 0
            ├─► [HR4]  Max 1 turno/día
            ├─► [HR5]  Max horas semanales       → Soft si permite_extra
            ├─► [HR6]  Max días semana
            ├─► [HR7]  Domingos libres (HARD)    → ≥2 libres/mes si régimen exceptuado y >20h/sem
            ├─► [HR8]  Cobertura mínima          → déficit penalizado
            ├─► [HR9]  Días consecutivos máx     → ventana deslizante
            ├─► [HR10] Descanso nocturno         → no diurno al día siguiente
            ├─► [HR11] Max domingos consecutivos → no más de 3 dom trabajados seguidos (Art. 38 inc. 5)
            │
            ├─► [SR1]  Turno Preferente          → penalización si no asignado
            ├─► [SR2]  Cambio de turno           → penalización por inconsistencia
            ├─► [SR3]  Turno dominante           → bonus por consistencia
            ├─► [SR4]  Día aislado               → penalización fragmentación
            ├─► [SR5]  Meta mensual              → penalización desviación
            ├─► [SR6]  Equidad por grupo         → minimiza rango max-min
            │
            └─► Minimize(deficits + excesos + penalizaciones - rewards)
                        │
                        ▼
                CpSolver.Solve(model)
                        │
                 OPTIMAL / FEASIBLE → asignaciones[]
                 INFEASIBLE         → error: no hay solución factible
```

---

## 4. CÓMO FUNCIONA EL MOTOR (builder.py)

### 4.1 Variable de Decisión

Para cada combinación de trabajador `w`, día `d` y turno `t`, el motor define una **variable binaria**:

```python
x[w, d, t] = model.NewBoolVar(f'x_{w}_{d}_{t}')
# x[w, d, t] = 1 → trabajador w trabaja el día d en turno t
# x[w, d, t] = 0 → no trabaja esa combinación
```

El espacio de búsqueda crece como: `|trabajadores| × |días| × |turnos|`

### 4.2 Fases de Construcción del Modelo

| Fase | Código | Descripción |
|---|---|---|
| 1. Carga de parámetros | `ConfigManager.preload()` | Lee los 43 parámetros desde la tabla `parametro_legal` en PostgreSQL. |
| 2. Pre-validación | `LegalEngine.turno_compatible(w, t)` | Verifica compatibilidad de cada trabajador con cada turno antes de construir el modelo. |
| 3. Restricciones duras | `HR1 ... HR11` | Añade constraints `model.Add(...)` que el solver no puede violar. |
| 4. Restricciones blandas | `SR1 ... SR6` | Añade variables de penalización que inflan el costo objetivo. |
| 5. Función objetivo | `model.Minimize(...)` | Suma ponderada de déficits, excesos y penalizaciones, menos rewards. |
| 6. Resolución | `CpSolver.Solve(model)` | OR-Tools ejecuta el backtracking con propagación de restricciones. Timeout: `SOLVER_TIMEOUT_SEG` segundos. |

### 4.3 Perfil Legal por Trabajador

El motor llama a `LegalEngine.resumen_legal(w_obj, turno_mock, dias_semana)` para obtener:

```python
res = {
    'max_horas_semana': 42.0,   # según TipoContrato
    'max_dias_semana':  6,       # según Código del Trabajo
    'aplica_domingo':   True,    # ← VER SECCIÓN 5: criterio legal correcto
    'min_domingos_mes': 2        # domingos libres obligatorios
}
```

El campo `permite_horas_extra` del trabajador convierte la restricción de horas semanales de **HARD → SOFT** (penalizada pero no infactible).

---

## 5. ORDEN DE EVALUACIÓN DE RESTRICCIONES (JERARQUÍA)

### Nivel 1 — Restricciones Legales (Duras, Irrompibles)

| ID | Nombre | Art. CT | Descripción |
|---|---|---|---|
| HR1 | Bloqueo por ausencia | — | Días con ausencia registrada: `x[w,d,t] = 0` para todos los turnos. |
| HR4 | Máximo 1 turno/día | Art. 22 | Un trabajador no puede estar en dos turnos simultáneos. |
| HR5 | Horas semanales máximas | Art. 28, Ley 21.561 | Full-time: ≤42h. Part-30: ≤30h. Part-20: ≤20h. Hard salvo `permite_horas_extra=True`. |
| HR6 | Días semana máximos | Art. 28 | Full-time: ≤6 días. Part-time: ≤5 días. |
| HR7 | Domingos libres obligatorios | Art. 38 inc. 4 | **Ver sección 5.1 — criterio y flujo completo.** |
| HR9 | Días consecutivos máx | Art. 38 | Ventana deslizante: no más de 6 días seguidos sin descanso. |
| HR10 | Descanso nocturno | Art. 28 | Turno nocturno en día D implica no turno diurno en D+1. |
| HR11 | Domingos consecutivos máx | Art. 38 inc. 5 | No más de 3 domingos trabajados en forma consecutiva. **NUEVO — ver sección 5.2.** |

### Nivel 2 — Restricciones de Empresa (Duras Configurables)

| ID | Nombre | Descripción |
|---|---|---|
| HR2 | Turno Fijo | Si el tipo es `turno_fijo`, el trabajador SÓLO puede trabajar ese turno. Su presencia es soft. |
| HR2b | Solo este Turno | `solo_turno`: en los días definidos, sólo se permite ese turno. |
| HR3 | Excluir Turno | `excluir_turno`: ese turno queda bloqueado para el trabajador en los días definidos. |
| HR1b | Dotación cero | Si la dotación de un turno en un día es 0, nadie puede ser asignado. |
| HR8 | Cobertura mínima | La suma de asignados por turno-día debe alcanzar la dotación requerida. |

### Nivel 3 — Preferencias Individuales (Blandas, Penalizadas)

| ID | Nombre | Peso default | Descripción |
|---|---|---|---|
| SR1 | Turno Preferente | `W_NO_PREFERENTE` = 500 | Si trabaja ese día pero en otro turno, se penaliza. |
| SR2 | Cambio de turno | `W_CAMBIO_TURNO` = 150 | Penaliza cambiar de tipo de turno entre días consecutivos. |
| SR3 | Turno dominante | `W_TURNO_DOMINANTE` = 80 | Bonus si un turno representa más del 50% de los días trabajados. |
| SR4 | Día aislado | `W_FRAG` = 100 | Penaliza trabajar un día rodeado de días libres. |
| SR5 | Meta mensual | `W_META` = 50.000 | Penaliza desviarse de la meta de días trabajados al mes. |
| SR6 | Equidad de grupo | `W_EQUIDAD` / `W_BALANCE` | Minimiza la diferencia de carga entre trabajadores del mismo tipo de contrato. |

### Nivel 4 — Función Objetivo

```python
model.Minimize(
    sum(deficits)        * W_DEFICIT  +  # Turno sin cubrir (catastrófico)
    sum(excesses)        * W_EXCESO   +  # Cobertura en exceso
    sum(rango_cargas)    * W_EQUIDAD  +  # Inequidad entre grupos
    sum(balance_turnos)  * W_BALANCE  +  # Inequidad por tipo de turno
    sum(desv_meta)       * W_META     +  # Desviación meta mensual
    sum(est_penalties)                +  # Cambios de turno, exceso horas
    sum(pref_penalties)               +  # Turnos no preferentes
    sum(frag_penalties)               -  # Días aislados
    sum(est_bonus)                    -  # Bonus turno dominante
    sum(reward_list)                     # Premio por cubrir turno (nocturno x2)
)
```

---

## 5.1 HR7 — FLUJO COMPLETO: DOMINGOS LIBRES OBLIGATORIOS (Art. 38 inc. 4)

### Criterio Legal Correcto

> **⚠️ CORRECCIÓN CRÍTICA respecto a versiones anteriores del documento.**
>
> El criterio de activación de HR7 **NO es `horas_semanales >= 30`**.
> Ese valor es incorrecto y no tiene base en el Código del Trabajo.

El Art. 38 inciso 4° CT establece textualmente:

> *"al menos dos de los días de descanso en el respectivo mes calendario deberán
> necesariamente otorgarse en día domingo. Esta norma **no se aplicará** respecto de
> los trabajadores cuya jornada ordinaria **no sea superior a veinte horas semanales**
> o se contraten exclusivamente para trabajar los días sábado, domingo o festivos."*

Los **dos requisitos copulativos** para que HR7 aplique son:

1. El trabajador pertenece a empresa en **régimen exceptuado** (Art. 38 N°2 o N°7 CT)
2. Su jornada ordinaria es **superior a 20 horas semanales** (`horas_semanales > 20`)

```python
# LegalEngine — criterio correcto
def aplica_domingo_obligatorio(trabajador) -> bool:
    return (
        trabajador.empresa.regimen_exceptuado  # Art. 38 N°2 o N°7
        and trabajador.horas_semanales > 20    # jornada > 20h/sem (no ">=30")
        and not trabajador.contrato_exclusivo_fds  # no contratado solo S/D/F
        and trabajador.plazo_contrato_dias > 30    # no contrato ≤30 días
    )
```

### Tabla de Casos por Tipo de Contrato

| Tipo contrato | Horas | Régimen exceptuado | ¿Aplica HR7? |
|---|---|---|---|
| Full-time | 42h | Sí | ✅ Sí |
| Part-time 30h | 30h | Sí | ✅ Sí (30 > 20) |
| Part-time 25h | 25h | Sí | ✅ Sí (25 > 20) |
| Part-time 20h | 20h | Sí | ❌ No (20 no es > 20) |
| Cualquiera | >20h | **No** | ❌ No (no es régimen exceptuado) |
| Contrato S/D/F exclusivo | Cualquiera | Sí | ❌ No (excepción expresa) |
| Contrato ≤30 días | Cualquiera | Sí | ❌ No (excepción expresa) |

### Flujo del Solver para Trabajadores con HR7 Activo

```
Para cada trabajador w con aplica_domingo_obligatorio = True:

1. Identificar todos los domingos del mes calendario:
   domingos_mes = [d for d in dias if d.weekday() == 6]

2. Identificar domingos bloqueados por ausencia (HR1):
   domingos_ausencia = [d for d in domingos_mes if (w.id, d) in bloqueados]
   # Estos domingos NO cuentan como "domingos libres otorgados"
   # (criterio: JLT Valdivia, I-23-2016)

3. Domingos disponibles para trabajar/librar:
   domingos_disponibles = domingos_mes - domingos_ausencia

4. Restricción HARD en el modelo:
   # De los domingos disponibles, al menos 2 deben ser libres
   model.Add(
       sum(
           1 - sum(x[w.id, d, t.id] for t in turnos)
           for d in domingos_disponibles
       ) >= MIN_DOMINGOS_LIBRES_MES  # = 2
   )

5. Por tanto, días que puede trabajar:
   max_domingos_trabajados = len(domingos_disponibles) - 2
```

### Interacción con Ausencias en Domingo

Este punto **no estaba documentado** en versiones anteriores y es crítico:

| Situación | Cuenta como dom. libre otorgado | Base legal |
|---|---|---|
| Ausencia por vacación legal | ❌ No cuenta | JLT Valdivia I-23-2016: las ausencias reducen el conteo disponible |
| Licencia médica | ❌ No cuenta | Mismo criterio |
| Permiso sin goce de sueldo | ❌ No cuenta (recomendación conservadora) | — |
| Día libre fijo (restricción HR2) | ✅ Sí cuenta | Es un descanso efectivamente otorgado |

**Impacto práctico**: Un mes con 4 domingos y 1 ausencia deja solo 3 domingos disponibles.
El trabajador puede trabajar máximo `3 - 2 = 1` domingo ese mes.

### Alerta de Pre-Validación (antes del Solver)

```python
def validar_domingos_factibles(trabajador, mes, anio, bloqueados):
    domingos = [d for d in dias_mes(mes, anio) if d.weekday() == 6]
    dom_disponibles = [d for d in domingos if (trabajador.id, d) not in bloqueados]
    dom_max_trabajados = max(0, len(dom_disponibles) - MIN_DOMINGOS_LIBRES_MES)

    if dom_max_trabajados == 0 and dotacion_dominical_requerida > 0:
        return Alerta(
            nivel="CRITICO",
            mensaje=f"{trabajador.nombre} no puede cubrir ningún domingo este mes "
                    f"({len(dom_disponibles)} domingos disponibles, 2 deben ser libres). "
                    f"Revisar ausencias o reasignar dotación dominical."
        )
```

---

## 5.2 HR11 — NUEVO: MÁXIMO DE DOMINGOS CONSECUTIVOS (Art. 38 inc. 5)

El Art. 38 inciso 5° CT establece (para trabajadores de casinos, hoteles, restaurantes, etc.):

> *"La distribución de los días domingos no podrá considerar la prestación de servicios
> por **más de tres domingos en forma consecutiva**."*

Si bien este inciso menciona específicamente esos rubros, la jurisprudencia de la DT lo
aplica extensivamente a los regímenes exceptuados del N°2 como criterio de buenas prácticas.

```python
# HR11 — Implementación en builder.py
# Para cada ventana de 4 domingos consecutivos, máximo 3 pueden ser trabajados
domingos_todos = sorted([d for d in dias if d.weekday() == 6])
for i in range(len(domingos_todos) - 3):
    ventana = domingos_todos[i:i+4]  # 4 domingos consecutivos
    model.Add(
        sum(
            sum(x[w.id, d, t.id] for t in turnos)
            for d in ventana
        ) <= 3  # máximo 3 de 4 domingos consecutivos
    )
```

---

## 5.3 DESCANSO COMPENSATORIO vs. DOMINGOS LIBRES OBLIGATORIOS

Estas son **dos obligaciones distintas** del Art. 38. No confundirlas:

| Concepto | Qué es | Parámetros que lo gestionan |
|---|---|---|
| **2 domingos libres/mes** (HR7) | En al menos 2 domingos del mes el trabajador no trabaja. Es un **descanso en domingo**. | `MIN_DOMINGOS_LIBRES_MES` |
| **Descanso compensatorio** | Por **cada domingo trabajado**, el empleador debe otorgar 1 día libre en la semana. Por cada festivo trabajado, otro día libre. | `COMP_PLAZO_DIAS_GENERAL`, `COMP_PLAZO_DIAS_EXCEPTUADO` |

```
Ejemplo: trabajador que trabaja 2 domingos en el mes
  → 2 domingos libres otorgados ✅ (cumple HR7)
  → 2 días compensatorios generados (uno por cada domingo trabajado)
  → Esos 2 días compensatorios deben darse dentro del plazo:
      - Régimen general: COMP_PLAZO_DIAS_GENERAL (15 días)
      - Régimen exceptuado: COMP_PLAZO_DIAS_EXCEPTUADO (30 días)
```

> **Nota de implementación**: El Solver actualmente gestiona los 2 domingos libres (HR7).
> Los días compensatorios generados por domingos trabajados son un proceso post-cuadrante
> que debe gestionarse en el módulo de compensaciones. El Solver no los modela directamente.

---

## 6. PRIORIDADES DEL MOTOR (QUÉ PRIVILEGIA)

| Conflicto | Resolución del Motor |
|---|---|
| Horas contratadas vs. cubrir un turno | `W_DEFICIT` (10M) > `W_EXCESO_HORAS` (20M). Si `permite_horas_extra=True`, el solver puede exceder; si es `False`, la restricción es HARD. |
| Día libre preferido vs. cobertura mínima | La cobertura gana siempre. El déficit de dotación es el costo más alto del sistema. |
| Domingos obligatorios vs. cobertura dominical | La regla de domingos libres es HARD. Si no se puede cubrir con los domingos disponibles → INFEASIBLE. |
| Turno Fijo vs. preferencia individual | El Turno Fijo es HARD para el tipo de turno. La preferencia individual tiene menor peso. |
| Trabajador sin disponibilidad suficiente | `validar_cobertura_factible()` lo detecta antes del solver. Si no se corrige → INFEASIBLE. |
| Part-time 20h con domingos | **HR7 no aplica** (jornada = 20h, no es > 20h). Puede ser asignado cualquier domingo. |
| Part-time >20h con domingos | **HR7 aplica** si la empresa es régimen exceptuado. Mínimo 2 domingos libres/mes. |
| Turno nocturno seguido de diurno | HARD (HR10). Nunca asignará turno diurno el día después de un nocturno. |
| 3 domingos consecutivos trabajados | HARD (HR11). El 4° domingo de una secuencia siempre será libre. |

---

## 7. DEFINICIÓN DE PARÁMETROS DE CONFIGURACIÓN

> **Nota**: Para ver los valores actuales en producción, consultar la BD:
> ```sql
> SELECT codigo, valor, categoria, descripcion FROM parametro_legal ORDER BY categoria, codigo;
> ```

### 7.1 Jornada y Horas

| Parámetro | Default | Descripción | Art. CT |
|---|---|---|---|
| `MAX_HRS_SEMANA_FULL` | 42.0 | Horas semanales máximas full-time | Art. 28, Ley 21.561 |
| `MAX_HRS_DIA_FULL` | 10.0 | Jornada diaria máxima full-time | Art. 28 |
| `MIN_DIAS_SEMANA_FULL` | 5.0 | Días mínimos en distribución semanal | Art. 28 |
| `MAX_DIAS_SEMANA_FULL` | 6.0 | Días máximos en distribución semanal | Art. 28 |
| `MAX_HRS_SEMANA_PART_TIME_30` | 30.0 | Horas máximas jornada parcial 30h | Art. 40 bis |
| `MAX_HRS_SEMANA_PART_TIME_20` | 20.0 | Horas máximas jornada reducida 20h | Art. 40 bis |
| `MAX_HRS_DIA_PART_TIME` | 10.0 | Jornada diaria máxima part-time | Art. 40 bis |
| `MAX_DIAS_SEMANA_PART` | 5.0 | Días máximos distribución semanal part-time | — |

### 7.2 Descansos y Domingos

| Parámetro | Default | Descripción | Art. CT |
|---|---|---|---|
| `MIN_DOMINGOS_LIBRES_MES` | 2.0 | Domingos libres mínimos por mes para trabajadores con HR7 activo | Art. 38 inc. 4 |
| `MIN_DESCANSO_ENTRE_TURNOS_HRS` | 12.0 | Horas mínimas entre dos turnos | Art. 28 |
| `MAX_DIAS_CONSECUTIVOS` | 6.0 | Días consecutivos máximos sin descanso | Art. 38 |
| `MAX_DOMINGOS_CONSECUTIVOS` | 3.0 | Domingos consecutivos máximos trabajados (HR11) | Art. 38 inc. 5 |
| `UMBRAL_HRS_DOMINGO_OBLIGATORIO` | 20.0 | **Umbral CORRECTO**: HR7 aplica si `horas_semanales > este_valor`. Valor legal = 20. NO modificar sin visar. | Art. 38 inc. 4 |
| `DOMINGOS_EXTRA_ANUALES_ART38BIS` | 7.0 | Domingos extra al año permitidos | Art. 38 bis |
| `MAX_DOMINGOS_SUSTITUIBLES_SABADO` | 1.0 | Domingos que pueden cambiarse por sábados (de los 7 extra) | Art. 38 bis |
| `COMP_PLAZO_DIAS_GENERAL` | 15.0 | Plazo para otorgar descanso compensatorio por dom. trabajado (régimen general) | Art. 38 inc. 3 |
| `COMP_PLAZO_DIAS_EXCEPTUADO` | 30.0 | Plazo para otorgar descanso compensatorio (régimen exceptuado) | Art. 38 inc. 3 |

> ⚠️ **Nota sobre `UMBRAL_HRS_DOMINGO_OBLIGATORIO`**: El umbral legal es estrictamente 20h.
> El inciso 4° del Art. 38 excluye a trabajadores con jornada "no superior a veinte horas",
> es decir, ≤20h. Por tanto, el umbral correcto en el sistema es `> 20` (no `>= 30`).
> Cambiar este valor requiere visación del responsable del proyecto.

### 7.3 Turno y Colación

| Parámetro | Default | Descripción | Art. CT |
|---|---|---|---|
| `MIN_HRS_TURNO_ABSOLUTO` | 4.0 | Mínimo de horas por turno | Art. 22 |
| `MIN_HRS_TURNO_CON_COLACION` | 6.0 | Mínimo de horas para tener derecho a colación | Art. 34 |
| `MIN_COLACION_MIN` | 30.0 | Mínimo de minutos de colación | Art. 34 |
| `MAX_COLACION_MIN` | 120.0 | Máximo de minutos de colación | Art. 34 |
| `HORA_INICIO_NOCTURNO` | 21.0 | Hora de inicio del tramo nocturno | — |
| `HORA_FIN_NOCTURNO` | 6.0 | Hora de término del tramo nocturno | — |

### 7.4 Estabilidad y Semana Corta

| Parámetro | Default | Descripción |
|---|---|---|
| `SEMANA_CORTA_UMBRAL_DIAS` | 5.0 | Umbral de días para considerar semana corta |
| `SEMANA_CORTA_PRORRATEO` | 1.0 | 1=aplica prorrateo en semana corta |
| `ESTAB_MIN_DIAS_MISMO_TURNO` | 3.0 | Mínimo de días en el mismo turno para estabilidad |
| `ESTAB_PENALTY_CAMBIO_TURNO` | 150.0 | Penalización por cambio de turno |
| `ESTAB_PENALTY_TURNO_AISLADO` | 200.0 | Penalización por turno aislado |
| `ESTAB_BONUS_TURNO_DOMINANTE` | 80.0 | Bonus por mantener turno dominante |
| `PREF_MIN_DIAS_BLOQUE` | 2.0 | Mínimo de días para bloque preferente |
| `PREF_MAX_DIAS_BLOQUE` | 6.0 | Máximo de días para bloque preferente |

### 7.5 Pesos del Motor

| Parámetro | Default | Descripción |
|---|---|---|
| `W_DEFICIT` | 10.000.000 | Costo por turno sin cubrir |
| `W_EXCESO` | 100.000 | Costo por exceso de cobertura |
| `W_EXCESO_HORAS` | 20.000.000 | Penalización por exceder jornada semanal |
| `W_EQUIDAD` | 1.000.000 | Penalización por inequidad mensual entre grupos |
| `W_BALANCE` | 3.000 | Penalización por inequidad de distribución por turno |
| `W_META` | 50.000 | Penalización por desviación de meta mensual |
| `W_REWARD` | 10.000 | Premio por cubrir un turno |
| `W_NOCHE_REWARD` | 20.000 | Premio extra por cubrir turno nocturno |
| `W_NO_PREFERENTE` | 500 | Penalización por turno no preferente |
| `W_CAMBIO_TURNO` | 150 | Penalización por cambio de tipo de turno |
| `W_TURNO_DOMINANTE` | 80 | Bonus por turno dominante |
| `SOFT_PENALTY_DIA_AISLADO` | 500 | Penalización por día de trabajo aislado |
| `SOFT_PENALTY_DESCANSO_AISLADO` | 300 | Penalización por día libre aislado |
| `SOFT_BONUS_BLOQUE_CONTINUO` | 1.000 | Bonus por bloques continuos de trabajo |

### 7.6 Operativos del Solver

| Parámetro | Default | Descripción |
|---|---|---|
| `SOLVER_TIMEOUT_SEG` | 60 | Tiempo máximo de ejecución del solver |
| `SOLVER_MAX_WORKERS` | 100 | Número máximo de trabajadores soportados |
| `DURACION_TURNO_PROMEDIO` | 8.0 | Duración estimada de turno para cálculos internos |

---

## 8. TIPOS DE RESTRICCIONES DE TURNO (enums.py)

Definidos en `app/models/enums.py` como `RestrictionType(str, Enum)`.

| Tipo | Valor BD | Naturaleza | Comportamiento en el Solver |
|---|---|---|---|
| `TURNO_FIJO` | `"turno_fijo"` | **Hard** | El trabajador SÓLO puede trabajar ese turno en los días definidos. Presencia es soft. |
| `SOLO_TURNO` | `"solo_turno"` | **Hard** | En los días definidos, sólo puede ser asignado a ese turno. |
| `EXCLUIR_TURNO` | `"excluir_turno"` | **Hard** | En los días definidos, ese turno queda bloqueado para el trabajador. |
| `TURNO_PREFERENTE` | `"turno_preferente"` | **Soft** | Si trabaja ese día pero en otro turno, se genera penalización de `W_NO_PREFERENTE`. |

```python
# Uso en builder.py — preparar_restricciones()
if r.tipo == RestrictionType.TURNO_FIJO:
    fijos[(w_id, d_str)] = r.turno.abreviacion           # Hard tipo, soft presencia
elif r.tipo == RestrictionType.SOLO_TURNO:
    turnos_bloqueados_por_dia[(w_id, d_str)] = {t_abrev} # Hard
elif r.tipo == RestrictionType.EXCLUIR_TURNO:
    restricciones_hard.append({'action': 'exclude', ...}) # Hard exclusión
elif r.tipo == RestrictionType.TURNO_PREFERENTE:
    restricciones_soft.append({'type': 'preferente', ...}) # Soft
```

---

## 9. CASOS BORDE DOCUMENTADOS

### Caso A — Full-time 42h, régimen exceptuado, trabaja domingos
- HR7 aplica: `42 > 20` y régimen exceptuado → 2 domingos libres/mes obligatorios.
- HR11 aplica: no puede trabajar más de 3 domingos consecutivos.
- En mes de 4 domingos: puede trabajar máximo 2 domingos.

### Caso B — Part-time 30h, turnos de 4h, trabaja domingos
- HR7 aplica: `30 > 20` y régimen exceptuado → 2 domingos libres/mes obligatorios.
- En mes de 4 domingos: puede trabajar máximo 2 domingos.
- Riesgo: cobertura dominical comprometida con muchos trabajadores de este perfil.

### Caso C — Part-time 20h, turnos de 4h, trabaja domingos
- HR7 **NO aplica**: `20` no es `> 20` → puede trabajar todos los domingos.
- Es el trabajador más valioso para cobertura dominical.
- Cuidado: no superar 6 días consecutivos sin descanso (HR9).

### Caso D — Part-time 20h, 5 turnos de 4h, trabaja domingos
- Misma lógica que Caso C: HR7 no aplica.
- **Tensión**: si trabaja 5 días incluyendo domingo, en semana con domingo libre
  solo puede completar 4×4h = 16h de las 20h contratadas.
- Resolución: el empleador no puede exigir recuperar esas 4h. El Builder
  reduce las horas esperadas de esa semana.
- Este es un caso extremo. Si el Solver lo detecta como infactible,
  el Admin debe ampliar disponibilidad o ajustar el contrato.

### Caso E — Mes con 4 domingos y 1 ausencia en domingo
- Domingos disponibles: 4 - 1 ausencia = 3 domingos efectivos.
- HR7: debe librar 2 de esos 3 → puede trabajar máximo 1 domingo ese mes.
- Si se necesitan 2 domingos trabajados → INFEASIBLE.
- Solución: ejecutar pre-validación antes del Solver para alertar al Admin.

### Caso F — Part-time 25h, régimen exceptuado
- **CASO NO MANEJADO en versiones anteriores del documento.**
- HR7 aplica: `25 > 20` → 2 domingos libres/mes obligatorios.
- En el sistema con el criterio incorrecto (`>= 30h`) este trabajador quedaba
  exento de HR7, lo cual era **ilegal**.
- Con el criterio corregido (`> 20h`), HR7 activa correctamente.

---

## 10. FLUJO DE DATOS RESUMIDO

```
SchedulingService.run_generation(mes, anio, sucursal_id)
  |
  +-- ConfigManager.preload()        <- SELECT * FROM parametro_legal
  +-- Trabajador.query(sucursal)     <- trabajadores_meta {horas, tipo, regimen_exceptuado}
  +-- Turno.query(sucursal)          <- turnos_meta {horas, nocturno, dotacion}
  +-- TrabajadorAusencia.query()     <- bloqueados [(w_id, fecha)]
  +-- TrabajadorRestriccionTurno()   <- fijos, r_hard, r_soft
  +-- coberturas = {fecha: {t: dotacion}}
  |
  +-- [PRE-VALIDACIÓN] validar_domingos_factibles()
  |   <- cruza ausencias dominicales con dotación requerida
  |   <- alerta al Admin si hay conflicto antes de lanzar el Solver
  |
  +-- build_model(...)
      |
      +-- x[w,d,t] en {0,1}      <- N_w x N_d x N_t variables binarias
      +-- HR1..HR11               <- restricciones duras (HR11 = NUEVO)
      +-- SR1..SR6                <- variables de penalización
      +-- Minimize(...)           <- función objetivo ponderada
      +-- CpSolver.Solve()        <- OR-Tools CP-SAT
          |
          +-- OPTIMAL/FEASIBLE    -> asignaciones [{trabajador_id, fecha, turno_id}]
          +-- INFEASIBLE          -> error: sin solución factible
```

---

## 11. MEJORAS IDENTIFICADAS

> Todas las mejoras deben ser aprobadas por el usuario antes de implementarse.

| ID | Prioridad | Título | Beneficio |
|---|---|---|---|
| MEJORA-01 | 🔴 Alta | **Corregir criterio HR7 en LegalEngine** | El criterio actual `horas >= 30` es incorrecto. Debe ser `regimen_exceptuado AND horas > 20`. Afecta trabajadores de 21-29h que hoy quedan exentos ilegalmente. |
| MEJORA-02 | 🔴 Alta | **Implementar HR11** (max 3 domingos consecutivos) | Obligación del Art. 38 inc. 5 CT no modelada actualmente. |
| MEJORA-03 | 🔴 Alta | **Validador previo al Solver con cruce de ausencias dominicales** | Evita lanzar el solver contra INFEASIBLE por falta de domingos disponibles. |
| MEJORA-04 | 🟠 Media | **Documentar y separar descanso compensatorio del módulo de domingos** | Los días compensatorios por domingos trabajados son una obligación distinta a los 2 domingos libres. Hoy los parámetros `COMP_PLAZO_*` existen pero no están documentados ni implementados. |
| MEJORA-05 | 🟠 Media | **Alerta de horas no completables (Part-Time en semana con domingo libre)** | Elimina penalizaciones falsas en `W_META` en semanas donde la ley obliga a librar el domingo. |
| MEJORA-06 | 🟠 Media | **Informe detallado de infactibilidad** | Permite corregir el conflicto sin investigación manual. |
| MEJORA-07 | 🟠 Media | **Suite de casos de prueba automatizados** | Garantiza que cambios al motor no rompan el comportamiento legal. Cubrir al menos los 6 casos borde de la sección 9. |
| MEJORA-08 | 🟡 Baja | **Panel de auditoría del cuadrante** | Valida legalidad del cuadrante antes de publicarlo. Muestra domingos libres utilizados por trabajador. |
| MEJORA-09 | 🟡 Baja | **Exportación a Excel con formato visual** | Facilita la comunicación del cuadrante a trabajadores y supervisores. |

---

## 12. NOTAS PARA EL IDE (CURSOR / WINDSURF / ANTIGRAVITY)

| Responsabilidad | Archivo correcto |
|---|---|
| Nueva restricción legal | `app/scheduler/builder.py` (series HR) |
| Cambiar criterio de domingos obligatorios | `app/services/legal_engine.py` → `aplica_domingo_obligatorio()` |
| Cambiar peso de optimización | `parametro_legal` en BD + `config_manager.py` |
| Nuevo tipo de restricción | `app/models/enums.py` → `RestrictionType` |
| Guardar restricción desde UI | `app/controllers/trabajador_bp.py` |
| Timeout del solver | Parámetro `SOLVER_TIMEOUT_SEG` en BD |
| Lógica de cálculo legal | `app/services/legal_engine.py` |
| Qué datos pasan al solver | `app/services/scheduling_service.py` |

**Archivos que NO contienen lógica de restricciones:**
- `app/templates/main/planificacion.html` → Solo UI
- `app/models/business.py` → Solo estructura de datos
- `app/models/core.py` → Solo geografía y feriados
- `app/controllers/main_bp.py` → Solo routing HTTP

**Consultar la BD cuando:**
- Se necesite verificar el valor actual de un parámetro legal.
- Se quiera auditar restricciones activas de un trabajador.
- Se investigue por qué el solver retornó INFEASIBLE.
- Se quiera verificar la dotación configurada por turno y día.

```sql
-- Parámetros actuales
SELECT codigo, valor, descripcion FROM parametro_legal ORDER BY categoria;

-- Restricciones activas de un trabajador
SELECT * FROM trabajador_restriccion_turno WHERE trabajador_id = :id AND activo = true;

-- Ausencias del período
SELECT * FROM trabajador_ausencia
WHERE trabajador_id = :id AND fecha_inicio <= :fin AND fecha_fin >= :inicio;

-- Verificar régimen exceptuado de empresa
SELECT id, nombre, regimen_exceptuado FROM empresa WHERE id = :id;
```

---

> [!CAUTION]
> **ADVERTENCIA FINAL**: Cualquier modificación al motor (`builder.py`), parámetros legales,
> jerarquía de restricciones, criterio de domingos obligatorios o función objetivo
> **DEBE ser visada y aprobada por el usuario responsable del proyecto**
> antes de ser implementada.
> Las modificaciones no autorizadas pueden generar cuadrantes ilegales que incumplan
> el Código del Trabajo chileno y expongan a la empresa a multas de la Dirección del Trabajo.

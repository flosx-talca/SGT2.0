# IMPLEMENTACIÓN FUTURA: Contexto Cross-Mes para Días Consecutivos (HR9)

> **Estado**: Pendiente de implementación
> **Prioridad**: Alta — afecta legalidad del primer tramo de cada mes planificado
> **Prerequisito**: El cuadrante generado debe persistirse en la BD antes de implementar esto.
> **Visación requerida**: Toda implementación debe ser aprobada por el usuario responsable del proyecto.

---

## 1. PROBLEMA

El Solver aplica correctamente HR9 (máximo 6 días consecutivos sin descanso) **dentro
del mes que está planificando**. Sin embargo, es **stateless entre meses**: no sabe
cuántos días consecutivos venía trabajando el trabajador al cierre del mes anterior.

Esto genera un **punto ciego legal** en el primer tramo de cada mes:

```
Mes anterior cierra con 5 días consecutivos trabajados:
  Mar 26 ✅  Mié 27 ✅  Jue 28 ✅  Vie 29 ✅  Sáb 30 ✅

Mes nuevo, el Solver asigna normalmente desde el día 1:
  Lun 1 ✅  Mar 2 ✅

Secuencia real: 26, 27, 28, 29, 30, 1, 2 → 7 días seguidos → ILEGAL ❌
Art. 38 CT: máximo 6 días consecutivos sin descanso.
```

**Frecuencia del problema**: Ocurre potencialmente todos los meses, en cualquier
semana que cruza el límite del calendario mensual.

---

## 2. BASE LEGAL

**Art. 38 CT — Días consecutivos máximos:**

> El trabajador no puede prestar servicios por más de **6 días consecutivos** sin
> gozar de un día de descanso.

El Código del Trabajo no reconoce el límite mensual como un reinicio de esta restricción.
La ventana de 6 días es **continua** y cruza los meses sin interrupción.

**Parámetro del sistema**: `MAX_DIAS_CONSECUTIVOS = 6` en `parametro_legal`.

---

## 3. PREREQUISITO: PERSISTENCIA DEL CUADRANTE EN BD

Antes de implementar esta funcionalidad, el sistema debe guardar el cuadrante generado
en la BD. Sin ese registro histórico, no es posible consultar los días trabajados al
cierre del mes anterior.

### Estructura mínima de tabla sugerida

```sql
CREATE TABLE cuadrante_asignacion (
    id               SERIAL PRIMARY KEY,
    trabajador_id    INTEGER NOT NULL REFERENCES trabajador(id),
    fecha            DATE NOT NULL,
    turno_id         INTEGER REFERENCES turno(id),  -- NULL = día libre
    es_libre         BOOLEAN NOT NULL DEFAULT FALSE,
    generado_en      TIMESTAMP DEFAULT NOW(),
    mes              INTEGER NOT NULL,
    anio             INTEGER NOT NULL,
    sucursal_id      INTEGER NOT NULL REFERENCES sucursal(id),
    UNIQUE (trabajador_id, fecha)
);

CREATE INDEX idx_cuadrante_trabajador_fecha
    ON cuadrante_asignacion(trabajador_id, fecha DESC);
```

> **Nota de diseño**: El campo `turno_id = NULL` con `es_libre = TRUE` representa
> un día libre planificado. Un `turno_id IS NOT NULL` representa un día trabajado.
> Esto permite distinguir "día libre planificado" de "fecha sin registro".

---

## 4. DISEÑO DE LA SOLUCIÓN

La solución tiene **3 componentes**:

```
[1] Al guardar el cuadrante]
    → Persistir asignaciones en cuadrante_asignacion

[2] Al iniciar una nueva planificación]
    → Consultar los últimos 6 días del mes anterior por trabajador
    → Calcular días_consecutivos_previos
    → Pasar ese contexto al Builder

[3] En el Builder]
    → Recibir dias_consecutivos_previos por trabajador
    → Restringir los primeros días del mes según el margen disponible
```

---

## 5. COMPONENTE 1: CONSULTA EN `scheduling_service.py`

```python
# app/services/scheduling_service.py

from datetime import date, timedelta
from calendar import monthrange

def obtener_dias_consecutivos_previos(
    trabajador_id: int,
    mes: int,
    anio: int,
    db_session
) -> int:
    """
    Consulta cuántos días consecutivos venía trabajando el trabajador
    al cierre del mes anterior.

    Retorna un entero entre 0 y MAX_DIAS_CONSECUTIVOS.
    Retorna 0 si no hay datos del mes anterior (primer cuadrante del sistema).

    Prerequisito: cuadrante_asignacion debe tener registros del mes anterior.
    """
    # Calcular rango del mes anterior
    if mes == 1:
        mes_anterior, anio_anterior = 12, anio - 1
    else:
        mes_anterior, anio_anterior = mes - 1, anio

    ultimo_dia_mes_ant = date(
        anio_anterior,
        mes_anterior,
        monthrange(anio_anterior, mes_anterior)[1]
    )
    inicio_ventana = ultimo_dia_mes_ant - timedelta(days=5)  # últimos 6 días

    # Consultar asignaciones de los últimos 6 días del mes anterior
    registros = db_session.execute("""
        SELECT fecha, turno_id
        FROM cuadrante_asignacion
        WHERE trabajador_id = :wid
          AND fecha BETWEEN :inicio AND :fin
        ORDER BY fecha DESC
    """, {
        "wid": trabajador_id,
        "inicio": inicio_ventana,
        "fin": ultimo_dia_mes_ant
    }).fetchall()

    if not registros:
        return 0  # Sin datos históricos → asumir sin racha previa

    # Contar días consecutivos trabajados desde el último día hacia atrás
    fechas_trabajadas = {r.fecha for r in registros if r.turno_id is not None}
    consecutivos = 0
    fecha_check = ultimo_dia_mes_ant

    while fecha_check >= inicio_ventana:
        if fecha_check in fechas_trabajadas:
            consecutivos += 1
            fecha_check -= timedelta(days=1)
        else:
            break  # Se rompió la racha

    return consecutivos
```

---

## 6. COMPONENTE 2: PASAR CONTEXTO AL BUILDER

```python
# app/services/scheduling_service.py — dentro de run_generation()

def run_generation(mes: int, anio: int, sucursal_id: int, db_session):

    trabajadores = Trabajador.query.filter_by(sucursal_id=sucursal_id, activo=True).all()

    # ... resto de la carga de datos existente ...

    # NUEVO: Contexto cross-mes por trabajador
    contexto_cross_mes = {}
    for w in trabajadores:
        contexto_cross_mes[w.id] = {
            "dias_consecutivos_previos": obtener_dias_consecutivos_previos(
                w.id, mes, anio, db_session
            )
        }

    # Pasar al builder
    resultado = build_model(
        trabajadores=trabajadores,
        # ... parámetros existentes ...
        contexto_cross_mes=contexto_cross_mes,   # NUEVO
    )
```

---

## 7. COMPONENTE 3: RESTRICCIÓN EN `builder.py`

```python
# app/scheduler/builder.py — dentro de build_model()

def build_model(
    trabajadores,
    dias,
    turnos,
    coberturas,
    bloqueados,
    config,
    contexto_cross_mes=None,   # NUEVO parámetro opcional
    **kwargs
):
    # ... código existente ...

    MAX_CONSECUTIVOS = int(config.get("MAX_DIAS_CONSECUTIVOS", 6))

    # ── HR9-CROSS: Restricción de días consecutivos cross-mes ─────────────────
    if contexto_cross_mes:
        for w in trabajadores:
            previos = contexto_cross_mes.get(w.id, {}).get("dias_consecutivos_previos", 0)

            if previos == 0:
                continue  # Sin racha previa, HR9 normal aplica desde el día 1

            margen = MAX_CONSECUTIVOS - previos
            # margen = cuántos días más puede trabajar antes de necesitar descanso

            if margen <= 0:
                # Ya viene con la racha completa: el día 1 del mes DEBE ser libre
                for t in turnos:
                    model.Add(x[w.id, dias[0], t.id] == 0)

            else:
                # Puede trabajar 'margen' días más, luego descanso obligatorio
                # Restricción: en los primeros (margen + 1) días,
                # al menos 1 debe ser libre
                primeros_dias = dias[:margen + 1]
                trabajados_en_ventana = [
                    sum(x[w.id, d, t.id] for t in turnos)
                    for d in primeros_dias
                ]
                model.Add(sum(trabajados_en_ventana) <= margen)
    # ─────────────────────────────────────────────────────────────────────────
```

---

## 8. CASOS Y COMPORTAMIENTO ESPERADO

| Días consecutivos al cierre del mes ant. | Margen disponible | Restricción al inicio del mes nuevo |
|---|---|---|
| 0 | 6 | Sin restricción adicional. HR9 normal. |
| 1 | 5 | Puede trabajar 5 días seguidos antes de descanso. |
| 3 | 3 | Puede trabajar 3 días seguidos antes de descanso. |
| 5 | 1 | Solo puede trabajar 1 día antes de descanso obligatorio. |
| 6 | 0 | El día 1 del mes nuevo **debe ser libre**. |

### Ejemplos concretos

```
Caso A — Cierra con 5 días consecutivos:
  previos = 5, margen = 1
  Primeros 2 días del mes: máximo 1 puede ser trabajado
  → Si trabaja día 1, día 2 debe ser libre
  → Si día 1 es libre, puede trabajar día 2 y 3 sin problema

Caso B — Cierra con 6 días consecutivos (máximo legal):
  previos = 6, margen = 0
  → Día 1 del mes nuevo = libre obligatorio (model.Add(x == 0))
  → Desde día 2 en adelante HR9 normal aplica

Caso C — Cierra con 0 días consecutivos (terminó en descanso):
  previos = 0
  → Sin restricción adicional, el mes comienza con hoja en blanco
```

---

## 9. PRE-VALIDACIÓN SUGERIDA

Antes de lanzar el Solver, alertar si el contexto cross-mes genera conflicto
con la dotación requerida en los primeros días del mes:

```python
def validar_consecutivos_cross_mes(
    trabajadores, dias, coberturas, contexto_cross_mes, config
):
    alertas = []
    MAX_CONS = int(config.get("MAX_DIAS_CONSECUTIVOS", 6))

    for w in trabajadores:
        previos = contexto_cross_mes.get(w.id, {}).get("dias_consecutivos_previos", 0)
        if previos < MAX_CONS:
            continue

        # Este trabajador DEBE descansar el día 1
        dia_1 = dias[0]
        demanda_dia_1 = sum(coberturas.get(dia_1, {}).values())

        if demanda_dia_1 > 0:
            alertas.append({
                "nivel": "ADVERTENCIA",
                "trabajador": w.nombre,
                "mensaje": (
                    f"Viene con {previos} días consecutivos del mes anterior. "
                    f"El día {dia_1.strftime('%d/%m/%Y')} debe ser libre obligatoriamente. "
                    f"No puede cubrir turnos ese día."
                )
            })
    return alertas
```

---

## 10. ORDEN DE IMPLEMENTACIÓN (cuando el cuadrante esté en BD)

1. **Crear tabla** `cuadrante_asignacion` con la estructura de la sección 3.
2. **Guardar cuadrante** al momento de confirmar la planificación generada.
3. **Implementar** `obtener_dias_consecutivos_previos()` en `scheduling_service.py`.
4. **Actualizar** `run_generation()` para calcular y pasar `contexto_cross_mes`.
5. **Agregar restricción** HR9-CROSS en `builder.py`.
6. **Agregar pre-validación** `validar_consecutivos_cross_mes()`.
7. **Test de regresión**: verificar que HR9 normal (dentro del mes) no se vea afectada.

---

## 11. TESTS DE ACEPTACIÓN

```
[TEST-HR9-CROSS-01]
  previos = 6, día 1 tiene demanda
  → Solver no asigna al trabajador el día 1
  → Solver asigna normalmente desde el día 2

[TEST-HR9-CROSS-02]
  previos = 5, días 1 y 2 tienen demanda
  → Solver asigna máximo 1 de los 2 primeros días
  → El otro queda libre

[TEST-HR9-CROSS-03]
  previos = 0
  → Sin cambio de comportamiento respecto al mes sin contexto

[TEST-HR9-CROSS-04]
  Sin registros en BD del mes anterior (primer cuadrante)
  → obtener_dias_consecutivos_previos() retorna 0
  → Sin restricción adicional

[TEST-HR9-CROSS-05]
  previos = 6, día 1 del mes = lunes, dotación mínima = 3 trabajadores
  → pre-validación genera alerta ADVERTENCIA para ese trabajador
  → Solver resuelve con los demás trabajadores disponibles
```

---

> **Recordatorio**: Este documento describe una implementación futura.
> No se debe implementar hasta que el cuadrante esté persistido en BD
> y el cambio sea visado por el usuario responsable del proyecto.

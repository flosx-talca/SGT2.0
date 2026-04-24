# Planificación y Cuadrante — Diseño e implementación

**Estado:** Pendiente
**Prioridad:** Alta — es el siguiente paso después de estabilizar el builder

---

## 1. Contexto

El sistema actualmente genera el cuadrante y lo muestra en pantalla (modo simulación),
pero no lo persiste en BD. Sin persistencia no es posible:

- Calcular horas por tipo (hábil, nocturna, domingo, feriado, extra)
- Gestionar compensatorios
- Construir dashboard de carga de trabajo
- Que el builder considere el último día del mes anterior
- Editar celdas manualmente con auditoría

---

## 2. Distinción de tablas — no mezclar responsabilidades

```
TrabajadorPreferencia  →  patrón recurrente por día de semana
                          "Pepito siempre los lunes trabaja turno M"
                          Sin fecha. El builder lo lee para construir FIJOS.

Cuadrante              →  registro real del mes publicado
                          "Pepito el lunes 7 de abril trabajó turno M"
                          Con fecha específica. La fuente de verdad operativa.
```

---

## 3. Modelo de datos

### 3.1 Tabla `Planificacion`

Cabecera del mes. Una por empresa/mes/año.

```python
class Planificacion(db.Model):
    __tablename__ = 'planificacion'

    id             = db.Column(db.Integer, primary_key=True)
    empresa_id     = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    mes            = db.Column(db.Integer, nullable=False)
    anio           = db.Column(db.Integer, nullable=False)
    estado         = db.Column(db.String(20), nullable=False, default='simulacion')
    # 'simulacion' → generado por solver, visible en pantalla, editable
    # 'publicado'  → oficial, horas calculadas, editable solo con override
    # 'cerrado'    → mes terminado, solo lectura

    publicado_en   = db.Column(db.DateTime)
    publicado_por  = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    creado_en      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)

    cuadrante = db.relationship('Cuadrante', backref='planificacion',
                                lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'mes', 'anio',
                            name='uq_planificacion_mes'),
    )
```

### 3.2 Tabla `Cuadrante`

Una fila por trabajador por día. Es la celda del cuadrante.

```python
class Cuadrante(db.Model):
    __tablename__ = 'cuadrante'

    id               = db.Column(db.Integer, primary_key=True)
    planificacion_id = db.Column(db.Integer, db.ForeignKey('planificacion.id'),
                                 nullable=False)
    trabajador_id    = db.Column(db.Integer, db.ForeignKey('trabajador.id'),
                                 nullable=False)
    turno_id         = db.Column(db.Integer, db.ForeignKey('turno.id'),
                                 nullable=True)    # null = libre o ausencia
    fecha            = db.Column(db.Date, nullable=False)

    # ── Origen de la asignación ───────────────────────────────────────────────
    origen           = db.Column(db.String(20), nullable=False)
    # 'solver'     → asignó el algoritmo
    # 'manual'     → usuario sobreescribió en el cuadrante
    # 'ausencia'   → vacaciones, licencia, compensatorio
    # 'libre'      → día de descanso

    # ── Asignación manual que viola reglas ───────────────────────────────────
    omite_validacion = db.Column(db.Boolean, default=False)
    motivo_override  = db.Column(db.String(255))   # obligatorio si omite_validacion=True

    # ── Horas calculadas al publicar (post_solver) ───────────────────────────
    horas_habil         = db.Column(db.Numeric(5,2), default=0)
    horas_nocturna      = db.Column(db.Numeric(5,2), default=0)
    horas_domingo       = db.Column(db.Numeric(5,2), default=0)
    horas_feriado       = db.Column(db.Numeric(5,2), default=0)
    horas_irrenunciable = db.Column(db.Numeric(5,2), default=0)
    horas_extra         = db.Column(db.Numeric(5,2), default=0)

    creado_en        = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en   = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    __table_args__ = (
        # Un trabajador solo puede tener una celda por día en una planificación
        db.UniqueConstraint('planificacion_id', 'trabajador_id', 'fecha',
                            name='uq_cuadrante_dia'),
        db.Index('ix_cuadrante_planificacion', 'planificacion_id'),
        db.Index('ix_cuadrante_trabajador',    'trabajador_id'),
        db.Index('ix_cuadrante_fecha',         'fecha'),
    )
```

---

## 4. Flujo completo publicar → calcular

```
1. Usuario revisa el cuadrante en simulación
2. Edita celdas si necesita (manual / override)
3. Hace clic en "Publicar"
4. Sistema:
   a. Crea registro Planificacion (estado='publicado')
   b. Para cada celda del cuadrante:
      → Crea registro Cuadrante con origen correcto
      → Calcula horas por tipo (hábil, nocturna, domingo, feriado)
      → Detecta horas extra si corresponde
   c. Genera compensatorios pendientes (domingo/feriado trabajado)
   d. Marca planificacion.estado = 'publicado'
```

---

## 5. Cálculo de horas por tipo al publicar

```python
def calcular_horas_celda(fecha, turno, feriados):
    """
    Dado un día y un turno, calcula las horas por tipo.
    Maneja turnos que cruzan medianoche.
    """
    cruza = turno.hora_fin <= turno.hora_inicio
    fecha_fin = fecha + timedelta(days=1) if cruza else fecha

    resultado = {
        'horas_habil': 0, 'horas_nocturna': 0,
        'horas_domingo': 0, 'horas_feriado': 0,
        'horas_irrenunciable': 0, 'horas_extra': 0
    }

    # Minutos en cada día
    mins_dia1 = (24*60) - (turno.hora_inicio.hour*60 + turno.hora_inicio.minute)
    mins_dia2 = turno.hora_fin.hour*60 + turno.hora_fin.minute if cruza else 0

    for d, mins in [(fecha, mins_dia1 if cruza else turno.duracion_horas*60),
                    (fecha_fin, mins_dia2)]:
        if mins == 0:
            continue
        tipo = _tipo_dia(d, feriados)
        resultado[f'horas_{tipo}'] += round(mins / 60, 2)

    return resultado


def _tipo_dia(fecha, feriados):
    if fecha in feriados and feriados[fecha]['es_irrenunciable']:
        return 'irrenunciable'
    if fecha in feriados:
        return 'feriado'
    if fecha.weekday() == 6:
        return 'domingo'
    # Horas nocturnas: entre 21:00 y 06:00 (definir según convenio)
    return 'habil'
```

---

## 6. Asignación manual con omisión de validación

Cuando el usuario asigna un turno manualmente saltándose una regla:

```
Sistema detecta la violación y avisa:
  "⚠️ Esta asignación viola [Ley 6×1: ya tiene 6 días consecutivos].
   ¿Desea continuar de todas formas?"

Usuario confirma → debe ingresar un motivo
Sistema guarda:
  origen = 'manual'
  omite_validacion = True
  motivo_override = "Emergencia operativa, sin reemplazante disponible"
```

Esto queda en auditoría permanente. No se puede borrar ni ocultar.

---

## 7. Restricciones por fecha específica (caso especial)

Un trabajador puede solicitar que durante un rango de fechas específico
solo se le asignen ciertos turnos. Ejemplo:

```
"La segunda semana de mayo solo quiero turno Mañana"
→ Del 12 al 18 de mayo, solo turno M
```

### ¿Afecta al builder actual?

**Sí, pero es fácil de integrar.** El pre-procesamiento `preparar_restricciones()`
ya clasifica días como FIJO. Solo hay que agregar una fuente más de FIJO:
además de los patrones por día de semana, también las restricciones por fecha específica.

### Tabla `RestriccionFecha`

```python
class RestriccionFecha(db.Model):
    __tablename__ = 'restriccion_fecha'

    id            = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajador.id'),
                              nullable=False)
    fecha_inicio  = db.Column(db.Date, nullable=False)
    fecha_fin     = db.Column(db.Date, nullable=False)
    turno_id      = db.Column(db.Integer, db.ForeignKey('turno.id'),
                              nullable=True)
    # turno_id = ID del turno → solo ese turno en ese rango
    # turno_id = None         → sin turno (días libres forzados en ese rango)

    motivo        = db.Column(db.String(255))   # opcional, para referencia
    activo        = db.Column(db.Boolean, default=True)
    creado_en     = db.Column(db.DateTime, default=datetime.utcnow)
```

### Integración en `preparar_restricciones()`

```python
# Después de procesar los patrones fijos por día de semana,
# agregar las restricciones por fecha específica:

for r in trabajador.restricciones_fecha:
    if not r.activo:
        continue
    curr = r.fecha_inicio
    while curr <= r.fecha_fin:
        fecha_str = curr.strftime('%Y-%m-%d')
        if fecha_str in dias_del_mes:
            if (t.id, fecha_str) not in bloqueados:
                if r.turno_id:
                    # Forzar turno específico esos días
                    fijos[(t.id, fecha_str)] = r.turno.abreviacion
                else:
                    # Forzar días libres esos días
                    bloqueados.add((t.id, fecha_str))
        curr += timedelta(days=1)
```

La lógica de `preparar_restricciones` ya maneja el conflicto:
BLOQUEADO > FIJO > LIBRE, por lo que si hay ausencia ese día, prevalece la ausencia.

---

## 8. Contexto del mes anterior en el builder

Si un trabajador terminó el mes anterior en su día 6 consecutivo,
el primer día del mes nuevo no puede trabajar.

```python
# En planificacion_bp.py, antes de llamar al builder:

def obtener_consecutivos_finales(trabajador_id, primer_dia_mes):
    """
    Cuenta cuántos días consecutivos terminó el trabajador
    al final del mes anterior.
    """
    dias_consec = 0
    fecha = primer_dia_mes - timedelta(days=1)  # último día del mes anterior

    while True:
        celda = Cuadrante.query.filter_by(
            trabajador_id=trabajador_id
        ).filter(
            Cuadrante.fecha == fecha,
            Cuadrante.origen.in_(['solver', 'manual'])
        ).first()

        if not celda or celda.turno_id is None:
            break   # día libre o ausencia → corta la racha

        dias_consec += 1
        fecha -= timedelta(days=1)

        if dias_consec >= 6:
            break

    return dias_consec

# Pasar al builder como contexto:
consecutivos_previos = {
    w: obtener_consecutivos_finales(w, primer_dia_mes)
    for w in t_ids
}
```

En el builder, HR6 ajusta la ventana inicial considerando los días previos:

```python
# HR6 con contexto del mes anterior:
for w in trabajadores:
    dias_previos = consecutivos_previos.get(w, 0)
    max_consec   = meta_w.get('max_dias_consecutivos', 6) or 6

    # Si terminó el mes anterior con N días consecutivos,
    # los primeros días de este mes reducen el margen disponible
    if dias_previos > 0:
        dias_restantes = max_consec - dias_previos
        if dias_restantes <= 0:
            # Debe empezar el mes con día libre obligatorio
            for t in turnos:
                model.Add(x[w, dias_del_mes[0], t] == 0)
        else:
            # La primera ventana es más corta
            primera_ventana = dias_del_mes[:dias_restantes + 1]
            model.Add(
                sum(x[w, d, t] for d in primera_ventana for t in turnos)
                <= dias_restantes
            )
```

---

## 9. Lo que habilita esta implementación

| Funcionalidad | Requiere |
|---|---|
| Guardar cuadrante publicado | Planificacion + Cuadrante |
| Edición manual con auditoría | Cuadrante.origen + omite_validacion |
| Cálculo de horas por tipo | Cuadrante.horas_* + post_solver |
| Compensatorios (domingo/feriado) | Cuadrante + tabla Compensatorio |
| Dashboard de carga | Cuadrante con horas calculadas |
| Restricción por rango de fechas | RestriccionFecha + preparar_restricciones |
| Contexto mes anterior en builder | Cuadrante + obtener_consecutivos_finales |
| Historial de planificaciones | Planificacion por empresa/mes/año |

---

## 10. Plan de implementación

### Paso 1 — Migración de BD
```
1a. Tabla Planificacion
1b. Tabla Cuadrante
1c. Tabla RestriccionFecha (para restricciones por fecha específica)
```

### Paso 2 — Endpoint /publicar
```
2a. Crear registro Planificacion
2b. Iterar celdas del cuadrante frontend → crear registros Cuadrante
2c. Calcular horas por tipo para cada celda con turno asignado
2d. Cambiar estado a 'publicado'
```

### Paso 3 — Edición manual con override
```
3a. Endpoint /cuadrante/celda actualiza Cuadrante existente
3b. Validar reglas antes de guardar
3c. Si viola regla → pedir confirmación + motivo
3d. Guardar con omite_validacion=True + motivo
```

### Paso 4 — Contexto mes anterior en builder
```
4a. Función obtener_consecutivos_finales()
4b. Pasar consecutivos_previos al builder
4c. Builder ajusta HR6 para primeros días del mes
```

### Paso 5 — RestriccionFecha en mantenedor
```
5a. Mantenedor UI para que el admin cargue restricciones por fecha
5b. Integrar en preparar_restricciones()
```

### Paso 6 — Dashboard
```
6a. Queries sobre Cuadrante agrupadas por trabajador/turno/mes
6b. KPIs: horas totales, por tipo, compensatorios pendientes
6c. Alertas: trabajadores sobre el límite, déficit de cobertura
```

---

## 11. Pendientes relacionados

- **Compensatorios:** tabla Compensatorio ya diseñada en documentación.
  Se genera automáticamente al publicar si hay domingos o feriados trabajados.
- **Horas extra:** requiere definir el umbral (¿sobre las horas contratadas del mes?
  ¿sobre el máximo semanal?). Pendiente de definición operativa.
- **Cierre de mes:** lógica para pasar estado de 'publicado' a 'cerrado'
  cuando el mes termina. Impide ediciones retroactivas no autorizadas.

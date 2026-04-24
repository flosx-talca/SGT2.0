# Mejora futura — Restricciones por fecha específica

**Estado:** Pendiente
**Prioridad:** Baja (el sistema funciona sin esto, es una mejora de calidad)

---

## 1. Qué es

Permite que un trabajador (o el administrador) defina que durante un rango
de fechas específico, solo se le asignen ciertos turnos o quede libre.

```
Ejemplo A — Solo turno mañana:
  "La segunda semana de mayo solo quiero turno M"
  → Del 12 al 18 de mayo, solo se le puede asignar turno M

Ejemplo B — Días libres forzados:
  "El 20 y 21 de junio no puedo trabajar (trámites personales)"
  → Esos días quedan bloqueados sin contar como ausencia formal

Ejemplo C — Solo turno nocturno ese período:
  "Las dos primeras semanas de julio solo puedo hacer turno N"
  → Del 1 al 14 de julio, solo turno N
```

---

## 2. Diferencia con lo que ya existe

| | TrabajadorPreferencia | RestriccionFecha |
|---|---|---|
| Granularidad | Día de semana (lunes, martes...) | Fecha específica (12/05/2026) |
| Recurrencia | Todos los meses, todos los lunes | Solo el rango indicado |
| Ejemplo | "Siempre los lunes → turno M" | "Del 12 al 18 de mayo → turno M" |
| Uso | Patrón operativo permanente | Solicitud puntual del trabajador |

---

## 3. Tabla `RestriccionFecha`

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
    # turno_id = ID del turno → solo ese turno en ese rango de fechas
    # turno_id = None         → días libres forzados en ese rango

    motivo        = db.Column(db.String(255))   # opcional, referencia interna
    activo        = db.Column(db.Boolean, default=True)
    creado_en     = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)

    trabajador = db.relationship('Trabajador', backref='restricciones_fecha',
                                 lazy=True)
```

---

## 4. Impacto en el builder

**El builder no cambia.** Solo cambia `preparar_restricciones()`.

La función ya clasifica cada `(trabajador, día)` en BLOQUEADO, FIJO o LIBRE.
`RestriccionFecha` es simplemente una fuente más que alimenta esa clasificación.

```python
# En preparar_restricciones(), después de procesar PatronSemanal:

for r in trabajador.restricciones_fecha:
    if not r.activo:
        continue
    curr = r.fecha_inicio
    while curr <= r.fecha_fin:
        fecha_str = curr.strftime('%Y-%m-%d')
        if fecha_str in dias_del_mes:
            if (trabajador.id, fecha_str) not in bloqueados:
                if r.turno_id:
                    # Solo ese turno esos días → FIJO
                    fijos[(trabajador.id, fecha_str)] = r.turno.abreviacion
                else:
                    # Días libres forzados → BLOQUEADO
                    bloqueados.add((trabajador.id, fecha_str))
        curr += timedelta(days=1)
```

---

## 5. Precedencia con otras restricciones

```
1. Ausencia formal (vacaciones, licencia)   → BLOQUEADO — máxima prioridad
2. RestriccionFecha con turno_id = None     → BLOQUEADO — libre forzado
3. RestriccionFecha con turno_id = X        → FIJO — turno específico
4. PatronSemanal (TrabajadorPreferencia)    → FIJO — patrón recurrente
5. LIBRE                                    → solver decide
```

Si hay conflicto entre una `RestriccionFecha` y un `PatronSemanal` para el
mismo día, la `RestriccionFecha` gana porque es más específica y más reciente.

---

## 6. Casos límite a considerar

**Conflicto con ausencia formal:**
Si hay una ausencia registrada para el mismo período, la ausencia prevalece.
`preparar_restricciones()` ya lo maneja — verifica `bloqueados` antes de aplicar FIJO.

**Restricción que excede el contrato:**
Si el trabajador tiene `RestriccionFecha` de "solo turno M" toda la semana
pero su contrato es de 30h (máx 4 días), el solver respetará el límite
contractual (HR5) y dejará algunos días de esa semana libres aunque estén
marcados como FIJO. Igual que con los PatronSemanal.

**Restricción en domingo:**
Los domingos se excluyen de los FIJO (igual que con PatronSemanal) para no
entrar en conflicto con HR7 (domingos libres mínimos). Si se necesita forzar
un turno el domingo, debe hacerse como edición manual en el cuadrante publicado.

---

## 7. Mantenedor UI

Pantalla dentro del mantenedor del trabajador, sección adicional debajo de
"Preferencias" y "Ausencias":

```
[+ Agregar restricción por fecha]

  Desde: [12/05/2026]  Hasta: [18/05/2026]
  Turno: [Mañana ▼]  (o "Libre" para forzar días libres)
  Motivo: [____________] (opcional)

  [Guardar]
```

Vista de restricciones existentes:
```
  12/05 → 18/05  Solo Mañana     [Editar] [Eliminar]
  20/06 → 21/06  Libre forzado   [Editar] [Eliminar]
```

---

## 8. Plan de implementación

```
1. Tabla RestriccionFecha → migración
2. Relación en modelo Trabajador → backref restricciones_fecha
3. Mantenedor UI → sección en modal-trabajador.html
4. preparar_restricciones() → agregar loop de RestriccionFecha
5. Validar conflictos en el mantenedor (fecha solapada con ausencia)
```

No requiere cambios en `builder.py` ni en `planificacion_bp.py`
más allá de `preparar_restricciones()`.

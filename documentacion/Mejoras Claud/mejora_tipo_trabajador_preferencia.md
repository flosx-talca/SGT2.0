# Mejora — Campo `tipo` en `TrabajadorPreferencia`

**Estado:** Realizado
**Fecha de finalización:** 2026-04-24
**Prioridad:** Alta (Implementada con éxito)
**Esfuerzo real:** 1 día

---

## 1. Problema actual

La tabla `TrabajadorPreferencia` no distingue entre tres comportamientos
distintos que el sistema necesita manejar:

| Caso | Comportamiento | Ejemplo |
|---|---|---|
| **Fijo** | DEBE trabajar ese día en ese turno | Recibe camiones lunes/mié/vie |
| **Solo turno** | Solo puede hacer ese turno (cualquier día) | Trabajador exclusivo de noche |
| **Preferencia** | Si trabaja ese día, solo puede ser ese turno | Si trabaja lunes, que sea M o T |

**Bug que genera:** un trabajador marcado para solo hacer turno N recibe
asignaciones de turno M porque `planificacion_bp.py` no construye
`turnos_permitidos` y el builder nunca aplica HR3.

---

## 2. Diferencia entre los tres tipos

```
FIJO:
  Lunes marcado T [Fijo]
  → x[w, lunes, T] = 1  ← OBLIGATORIO, el solver no puede ignorarlo
  → x[w, lunes, M] = 0
  → x[w, lunes, I] = 0
  → x[w, lunes, N] = 0
  → Trabaja sí o sí ese día en ese turno

SOLO_TURNO:
  Todos los días marcado N [Solo turno]
  → x[w, d, M] = 0  todos los días ← BLOQUEADO
  → x[w, d, T] = 0  todos los días ← BLOQUEADO
  → x[w, d, I] = 0  todos los días ← BLOQUEADO
  → x[w, d, N] = libre ← solver decide si trabaja O descansa
  → Cuando descansa, el solver busca otro trabajador para cubrir N

PREFERENCIA:
  Lunes marcado M y T [Preferencia]
  → x[w, lunes, I] = 0  ← bloqueado ese día
  → x[w, lunes, N] = 0  ← bloqueado ese día
  → x[w, lunes, M] = libre  ← puede trabajar M o descansar
  → x[w, lunes, T] = libre  ← puede trabajar T o descansar
  → No es obligatorio trabajar, pero si trabaja, solo M o T
```

---

## 3. Los tipos van en duro en el código (no en BD)

Son exactamente 3, no van a cambiar, son un concepto del motor.

```python
# app/models/business.py o constants.py
TIPO_PREFERENCIA_CHOICES = [
    ('preferencia', 'Preferencia'),       # si trabaja, solo estos turnos ese día
    ('fijo',        'Fijo obligatorio'),  # DEBE trabajar ese día ese turno
    ('solo_turno',  'Solo este turno'),   # cualquier día solo puede hacer este turno
]
```

---

## 4. Cambio en el modelo

```python
class TrabajadorPreferencia(db.Model):
    __tablename__ = 'trabajador_preferencia'

    id            = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer,
                              db.ForeignKey('trabajador.id', ondelete='CASCADE'),
                              nullable=False)
    dia_semana    = db.Column(db.Integer, nullable=False)   # 0=Lun, 6=Dom
    turno         = db.Column(db.String(5), nullable=False)

    # NUEVO: tipo de restricción
    tipo          = db.Column(db.String(20), nullable=False, default='preferencia')
    # 'preferencia' → si trabaja ese día, solo estos turnos
    # 'fijo'        → DEBE trabajar ese día ese turno (HARD)
    # 'solo_turno'  → solo puede hacer este turno cualquier día
```

---

## 5. Migración de BD

```python
"""add tipo to trabajador_preferencia

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision      = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on    = None


def upgrade():
    # Agregar columna tipo con default 'preferencia'
    op.add_column(
        'trabajador_preferencia',
        sa.Column('tipo', sa.String(20), nullable=False,
                  server_default='preferencia')
    )

    # Todos los registros existentes quedan como 'preferencia'
    # (comportamiento más conservador, no fuerza ni restringe)
    op.execute(text("""
        UPDATE trabajador_preferencia
        SET tipo = 'preferencia'
        WHERE tipo IS NULL
    """))

    print("✅ Campo tipo agregado a trabajador_preferencia")


def downgrade():
    op.drop_column('trabajador_preferencia', 'tipo')
```

---

## 6. Cambios en `preparar_restricciones()`

```python
def preparar_restricciones(trabajadores_db, dias_del_mes, ausencias):
    """
    Pre-procesamiento ANTES del solver.
    Ahora distingue los 3 tipos de preferencia.
    """
    bloqueados = set()
    fijos      = {}
    turnos_bloqueados_por_dia = {}  # { (worker_id, fecha): set(turnos_bloqueados) }

    domingos_mes = {
        d for d in dias_del_mes
        if cal_module.weekday(int(d[:4]), int(d[5:7]), int(d[8:10])) == 6
    }

    for t in trabajadores_db:

        # ── BLOQUEADOS: ausencias ─────────────────────────────────────────
        for (w_id, fecha_str) in ausencias:
            if w_id == t.id:
                bloqueados.add((t.id, fecha_str))

        # ── Agrupar preferencias por día de semana y tipo ─────────────────
        prefs_por_dia   = {}  # { dia_semana: { tipo: [turnos] } }
        turnos_solo     = []  # turnos de tipo 'solo_turno'

        for p in t.preferencias:
            if p.tipo == 'solo_turno':
                turnos_solo.append(p.turno)
            else:
                if p.dia_semana not in prefs_por_dia:
                    prefs_por_dia[p.dia_semana] = {'fijo': [], 'preferencia': []}
                prefs_por_dia[p.dia_semana][p.tipo].append(p.turno)

        # ── Procesar FIJOS y PREFERENCIAS por día de semana ──────────────
        for dia_str in dias_del_mes:
            if dia_str in domingos_mes:
                continue
            if (t.id, dia_str) in bloqueados:
                continue

            py_weekday = cal_module.weekday(
                int(dia_str[:4]), int(dia_str[5:7]), int(dia_str[8:10])
            )

            if py_weekday not in prefs_por_dia:
                continue

            prefs_dia = prefs_por_dia[py_weekday]

            # FIJO: DEBE trabajar ese día ese turno
            if prefs_dia['fijo']:
                # Solo puede haber 1 turno fijo por día
                t_fijo = prefs_dia['fijo'][0]
                fijos[(t.id, dia_str)] = t_fijo

            # PREFERENCIA: si trabaja, solo estos turnos
            elif prefs_dia['preferencia']:
                # Guardar qué turnos están PERMITIDOS ese día
                # El builder bloqueará los que no están en este set
                key = (t.id, dia_str)
                if key not in turnos_bloqueados_por_dia:
                    turnos_bloqueados_por_dia[key] = set(prefs_dia['preferencia'])

        # ── SOLO_TURNO: aplica todos los días ────────────────────────────
        # Se pasa a trabajadores_meta como turnos_permitidos
        # El builder bloquea todos los demás turnos todos los días
        if turnos_solo:
            # Guardar en el objeto trabajador para que planificacion_bp lo lea
            t._turnos_solo = list(set(turnos_solo))
        else:
            t._turnos_solo = None

    return bloqueados, fijos, turnos_bloqueados_por_dia
```

---

## 7. Cambios en `builder.py`

### Nueva regla HR2b — Preferencia de turno por día

```python
# ════════════════════════════════════════════════════════════════════════════
# HR2: FIJOS → x=1 en turno fijo, x=0 en el resto (sin cambios)
# ════════════════════════════════════════════════════════════════════════════
for (w, d), t_fijo in fijos.items():
    if w in trabajadores and d in dias_del_mes and t_fijo in turnos:
        model.Add(x[w, d, t_fijo] == 1)
        for t_otro in turnos:
            if t_otro != t_fijo:
                model.Add(x[w, d, t_otro] == 0)

# ════════════════════════════════════════════════════════════════════════════
# HR2b: PREFERENCIA por día → bloquear turnos NO permitidos ese día
# Si el trabajador tiene preferencia[lunes] = {M, T}
# → bloquear I y N ese lunes (pero puede quedar libre)
# ════════════════════════════════════════════════════════════════════════════
for (w, d), turnos_permitidos_dia in turnos_bloqueados_por_dia.items():
    if w in trabajadores and d in dias_del_mes:
        for t in turnos:
            if t not in turnos_permitidos_dia:
                model.Add(x[w, d, t] == 0)
```

### HR3 — Solo turno (ya existe, ahora llega el dato)

```python
# ════════════════════════════════════════════════════════════════════════════
# HR3: Turnos no permitidos por trabajador (solo_turno)
# ════════════════════════════════════════════════════════════════════════════
for w in trabajadores:
    permitidos = trabajadores_meta.get(w, {}).get('turnos_permitidos', None)
    if permitidos:
        for d in dias_del_mes:
            for t in turnos:
                if t not in permitidos:
                    model.Add(x[w, d, t] == 0)
```

### Nueva firma de `build_model`

```python
def build_model(trabajadores, dias_del_mes, turnos, coberturas,
                bloqueados, fijos,
                turnos_bloqueados_por_dia,   # ← nuevo parámetro
                reglas=None, trabajadores_meta=None, turnos_meta=None):
```

---

## 8. Cambios en `planificacion_bp.py`

```python
# Llamar a preparar_restricciones con nueva firma
bloqueados, fijos, turnos_bloqueados_por_dia = preparar_restricciones(
    trabajadores_db, dias_del_mes, ausencias
)

# Construir trabajadores_meta con turnos_permitidos desde solo_turno
trabajadores_meta = {
    t.id: {
        'horas_semanales':   t.horas_semanales or 42,
        'turnos_permitidos': t._turnos_solo,  # None o ['N']
    }
    for t in trabajadores_db
}

# Pasar turnos_bloqueados_por_dia al builder
model, x = build_model(
    t_ids,
    dias_del_mes,
    turnos,
    coberturas_por_dia,
    bloqueados,
    fijos,
    turnos_bloqueados_por_dia,   # ← nuevo
    reglas=reglas_bd,
    trabajadores_meta=trabajadores_meta,
    turnos_meta=turnos_meta,
)
```

---

## 9. Cambios en el mantenedor del trabajador

### UI — tabla con columna `tipo`

```html
<!-- Dentro del modal-trabajador.html -->
<!-- Sección de patrones de turno -->

<p class="small text-muted mb-2">
  <strong>Sin marca en un día</strong> → solver libre, cualquier turno.<br>
  <strong>Con marca</strong> → depende del tipo seleccionado.
</p>

<table class="table table-sm table-bordered align-middle">
  <thead class="table-light">
    <tr>
      <th>Día</th>
      {% for t in tipos_turno %}
      <th class="text-center">
        <span class="badge" style="background-color: {{ t.color }}">{{ t.abreviacion }}</span>
      </th>
      {% endfor %}
      <th>Tipo</th>
    </tr>
  </thead>
  <tbody>
    {% set dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'] %}
    {% for i in range(7) %}
    <tr>
      <td class="fw-bold small">{{ dias[i] }}</td>
      {% for t in tipos_turno %}
      <td class="text-center">
        <input type="checkbox"
               name="pref_{{ i }}[]"
               value="{{ t.abreviacion }}"
               {% if registro %}
                 {% for p in registro.preferencias %}
                   {% if p.dia_semana == i and p.turno == t.abreviacion %}checked{% endif %}
                 {% endfor %}
               {% endif %}>
      </td>
      {% endfor %}
      <td>
        <select name="pref_tipo_{{ i }}" class="form-select form-select-sm"
                id="tipo_dia_{{ i }}" onchange="actualizarTipoDia({{ i }})">
          <option value="preferencia">Preferencia</option>
          <option value="fijo"
            {% if registro %}
              {% for p in registro.preferencias %}
                {% if p.dia_semana == i and p.tipo == 'fijo' %}selected{% endif %}
              {% endfor %}
            {% endif %}>Fijo obligatorio</option>
          <option value="solo_turno"
            {% if registro %}
              {% for p in registro.preferencias %}
                {% if p.dia_semana == i and p.tipo == 'solo_turno' %}selected{% endif %}
              {% endfor %}
            {% endif %}>Solo este turno</option>
        </select>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<!-- Tooltip explicativo -->
<div class="alert alert-light border small mt-2">
  <strong>Preferencia:</strong> si trabaja ese día, solo puede ser ese turno.<br>
  <strong>Fijo obligatorio:</strong> DEBE trabajar ese día en ese turno (ej: recibe camiones).<br>
  <strong>Solo este turno:</strong> cualquier día que trabaje, solo puede ser ese turno (ej: solo noche).
</div>
```

### JavaScript — validación en UI

```javascript
function actualizarTipoDia(dia) {
    const tipo      = $(`#tipo_dia_${dia}`).val();
    const checkboxes = $(`input[name="pref_${dia}[]"]`);

    if (tipo === 'fijo') {
        // Fijo: solo puede haber 1 turno seleccionado
        checkboxes.on('change', function() {
            if ($(this).is(':checked')) {
                checkboxes.not(this).prop('checked', false);
            }
        });
        // Si hay más de uno marcado, dejar solo el primero
        const marcados = checkboxes.filter(':checked');
        if (marcados.length > 1) {
            marcados.not(':first').prop('checked', false);
            toastr.warning('Fijo obligatorio: solo puede seleccionar un turno por día.');
        }
    }

    if (tipo === 'solo_turno') {
        // Solo turno: si marca uno, se aplica igual en todos los días
        toastr.info('Solo este turno aplica para todos los días de la semana.');
    }
}
```

### Backend — guardar con tipo

```python
# En trabajador_bp.py, sección procesar preferencias:

TrabajadorPreferencia.query.filter_by(trabajador_id=trabajador.id).delete()
for i in range(7):
    prefs  = request.form.getlist(f'pref_{i}[]')
    tipo_i = request.form.get(f'pref_tipo_{i}', 'preferencia')

    for p in prefs:
        db.session.add(TrabajadorPreferencia(
            trabajador_id = trabajador.id,
            dia_semana    = i,
            turno         = p,
            tipo          = tipo_i
        ))
```

---

## 10. Casos de prueba

| Configuración | Resultado esperado |
|---|---|
| Sin ninguna marca | Solver libre, cualquier turno cualquier día |
| Lunes: M,T [Preferencia] | El lunes solo puede ser M o T (o libre) |
| Lunes: N [Fijo] | El lunes DEBE trabajar N, siempre |
| Todos los días: N [Solo turno] | Solo puede hacer N, puede descansar |
| Lunes: T [Fijo] + resto: N [Solo turno] | Lunes obligatorio T, otros días solo N o libre |
| Lunes: M,T [Fijo] con 2 marcas | UI avisa: fijo solo permite 1 turno |

---

## 11. Resumen de archivos a modificar

| Archivo | Cambio |
|---|---|
| `app/models/business.py` | Agregar campo `tipo` a `TrabajadorPreferencia` |
| `migrations/versions/c3d4e5f6a7b8_*.py` | Migración nueva |
| `app/scheduler/builder.py` | HR2b nuevo + nueva firma con `turnos_bloqueados_por_dia` |
| `app/scheduler/builder.py` → `preparar_restricciones()` | Distinguir 3 tipos |
| `app/controllers/planificacion_bp.py` | Construir `turnos_permitidos` + pasar `turnos_bloqueados_por_dia` |
| `app/controllers/trabajador_bp.py` | Guardar `tipo` al procesar preferencias |
| `app/templates/modal-trabajador.html` | Columna `tipo` en tabla de preferencias |

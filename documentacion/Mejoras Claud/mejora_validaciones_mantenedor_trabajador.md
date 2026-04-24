# Mejoras — Validaciones en mantenedor del trabajador

**Estado:** Pendiente
**Prioridad:** Alta — previene INFEASIBLE en el builder
**Esfuerzo estimado:** 1 día

---

## 1. Contexto

El mantenedor del trabajador permite configurar patrones de turno con tres
tipos: `fijo`, `solo_turno` y `preferencia`. Sin validaciones, un operador
puede configurar más días fijos de los que el contrato del trabajador permite,
causando INFEASIBLE en el builder sin una explicación clara para el usuario.

---

## 2. Principio fundamental — sin valores hardcodeados

**Las horas por turno las define el usuario** en el mantenedor de turnos,
no el sistema. La duración de cada turno se calcula desde `hora_inicio`
y `hora_fin`:

```
Usuario crea turno Mañana:   07:00 → 15:00 = 8h
Usuario crea turno Medio:    08:00 → 14:00 = 6h
Usuario crea turno Noche:    23:00 → 07:00 = 8h (cruza medianoche)
```

Por lo tanto `max_fijos` cambia según la empresa:

```
Empresa A — turnos de 8h, trabajador 42h:
  max_fijos = ceil(42 / 8) = 6

Empresa B — turnos de 6h, trabajador 42h:
  max_fijos = ceil(42 / 6) = 7

Empresa C — turnos mixtos (6h y 8h):
  promedio  = (6 + 8 + 6 + 8) / 4 = 7h
  max_fijos = ceil(42 / 7) = 6
```

---

## 3. Función compartida — `app/utils.py`

La función que calcula la duración del turno existe en `planificacion_bp.py`
como `_calcular_horas_turno`. Debe moverse a un lugar compartido para que
tanto el blueprint de planificación como el de trabajadores la reutilicen:

```python
# app/utils.py  ← crear este archivo
def calcular_horas_turno(hora_inicio, hora_fin):
    """
    Calcula la duración en horas de un turno.
    Maneja el caso que cruza medianoche (hora_fin <= hora_inicio).
    hora_inicio y hora_fin son objetos datetime.time.

    Ejemplos:
      07:00 → 15:00 = 8h
      23:00 → 07:00 = 8h  (cruza medianoche)
      08:00 → 14:00 = 6h
    """
    h_ini = hora_inicio.hour * 60 + hora_inicio.minute
    h_fin = hora_fin.hour    * 60 + hora_fin.minute
    if h_fin <= h_ini:
        h_fin += 24 * 60
    return (h_fin - h_ini) / 60
```

Actualizar `planificacion_bp.py` para importarla:

```python
# planificacion_bp.py — reemplazar función local por importación
from app.utils import calcular_horas_turno
# Eliminar la definición local de _calcular_horas_turno
```

---

## 4. Validación 1 — Máximo fijos según horas contratadas

### Regla

El número de días fijos por semana no puede superar los turnos que
corresponden al contrato del trabajador:

```
max_fijos_semana = ceil(horas_semanales / duracion_promedio_turnos)
```

### Por qué

Si hay más fijos que días permitidos por contrato, HR2-FIJO (HARD) y
HR10 (total mensual) se contradicen → INFEASIBLE garantizado.

```
Part-time 32h, turnos de 8h, meta = 18 días/mes, 5 fijos/semana:
  fijos reales ≈ 21 días
  meta contrato = 18 días
  21 > 18 → INFEASIBLE ❌

Part-time 32h, turnos de 8h, meta = 18 días/mes, 4 fijos/semana:
  fijos reales ≈ 17 días
  meta contrato = 18 días
  17 ≤ 18 → OK ✅
```

### Backend — `trabajador_bp.py`

```python
import math
from app.utils import calcular_horas_turno
from app.models.business import Turno

@trabajador_bp.route('/modal', methods=['POST'])
def modal():
    ...
    # Calcular duración promedio de los turnos de la empresa
    empresa_id = registro.empresa_id if registro else None
    turnos_db  = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all() \
                 if empresa_id else []

    duraciones = [
        calcular_horas_turno(t.hora_inicio, t.hora_fin)
        for t in turnos_db
    ]
    duracion_promedio = round(sum(duraciones) / len(duraciones)) if duraciones else 8

    horas     = registro.horas_semanales if registro else 42
    max_fijos = math.ceil(horas / duracion_promedio)

    return render_template('modal-trabajador.html',
                           ...,
                           max_fijos=max_fijos,
                           duracion_turno=duracion_promedio)


@trabajador_bp.route('/guardar', methods=['POST'])
def guardar():
    ...
    horas_str  = request.form.get('horas_semanales', '42').strip()
    horas      = int(horas_str) if horas_str else 42
    empresa_id = request.form.get('empresa_id', '').strip()

    # Calcular duración promedio de los turnos de la empresa
    turnos_db  = Turno.query.filter_by(empresa_id=int(empresa_id), activo=True).all()
    duraciones = [calcular_horas_turno(t.hora_inicio, t.hora_fin) for t in turnos_db]
    duracion   = round(sum(duraciones) / len(duraciones)) if duraciones else 8
    max_fijos  = math.ceil(horas / duracion)

    # Contar días fijos configurados
    fijos_semana = sum(
        1 for i in range(7)
        if request.form.get(f'pref_tipo_{i}') == 'fijo'
        and request.form.getlist(f'pref_{i}[]')
    )

    if fijos_semana > max_fijos:
        return jsonify({
            'ok':  False,
            'msg': f'Con {horas}h semanales y turnos de ~{duracion}h, '
                   f'este trabajador puede tener máximo {max_fijos} días '
                   f'fijos por semana (configurados: {fijos_semana}).'
        }), 400

    # Validar domingo
    if request.form.get('pref_tipo_6') == 'fijo':
        return jsonify({
            'ok':  False,
            'msg': 'Los domingos no pueden ser días fijos. '
                   'El sistema gestiona los domingos automáticamente.'
        }), 400
    ...
```

### Frontend — `modal-trabajador.html`

```html
<!-- Indicador debajo de la tabla de preferencias -->
<div class="d-flex justify-content-between align-items-center mt-2">
    <small id="info_max_fijos" class="text-muted">
        0 de {{ max_fijos }} días fijos disponibles
    </small>
    <small class="text-muted fst-italic">
        Límite según horas del contrato y duración de turnos
    </small>
</div>

<script>
// Valores calculados en el backend — no hardcodeados
const duracionTurno  = {{ duracion_turno }};
const turnosNocturnos = {{ turnos_nocturnos | tojson }};

// Actualizar max_fijos cuando cambian las horas del contrato
$('#horas_semanales').on('input change', function() {
    const horas    = parseInt($(this).val()) || 42;
    const maxFijos = Math.ceil(horas / duracionTurno);
    validarFijosUI(maxFijos);
});

// Contar fijos actuales y actualizar indicador
function validarFijosUI(maxFijos) {
    let totalFijos = 0;
    for (let i = 0; i < 7; i++) {
        const tipo    = $(`#tipo_dia_${i}`).val();
        const marcado = $(`input[name="pref_${i}[]"]:checked`).length > 0;
        if (tipo === 'fijo' && marcado) totalFijos++;
    }

    const $info = $('#info_max_fijos');
    if (totalFijos > maxFijos) {
        $info.text(`⚠️ ${totalFijos} días fijos — excede el máximo de ${maxFijos}`)
             .removeClass('text-muted').addClass('text-danger fw-bold');
        return false;
    }
    $info.text(`${totalFijos} de ${maxFijos} días fijos disponibles`)
         .removeClass('text-danger fw-bold').addClass('text-muted');
    return true;
}

// Llamar validación al cambiar tipo de día
function onChangeTipoDia(dia) {
    const horas    = parseInt($('#horas_semanales').val()) || 42;
    const maxFijos = Math.ceil(horas / duracionTurno);
    validarFijosUI(maxFijos);

    // Bloquear fijo en domingo
    if (dia === 6 && $(`#tipo_dia_${dia}`).val() === 'fijo') {
        toastr.warning('Los domingos no pueden ser días fijos.');
        $(`#tipo_dia_${dia}`).val('preferencia');
    }
}

// Validar antes de guardar
function guardarTrabajador() {
    const horas    = parseInt($('#horas_semanales').val()) || 42;
    const maxFijos = Math.ceil(horas / duracionTurno);

    if (!validarFijosUI(maxFijos)) {
        toastr.error(
            `Máximo ${maxFijos} días fijos con ${horas}h semanales. ` +
            `Reduzca los días fijos o aumente las horas del contrato.`
        );
        return;
    }

    // Advertir si hay fijo diurno (posible conflicto con noche día anterior)
    detectarConflictoNoche();

    // ... resto del guardar
}

// Advertencia por fijo diurno (no bloqueante — decisión del operador)
function detectarConflictoNoche() {
    const diasNombres  = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
    const diasConFijo  = [];

    for (let i = 0; i < 7; i++) {
        const tipo   = $(`#tipo_dia_${i}`).val();
        const turnos = $(`input[name="pref_${i}[]"]:checked`)
                       .map(function() { return $(this).val(); }).get();
        const tieneDiurno = turnos.some(t => !turnosNocturnos.includes(t));
        if (tipo === 'fijo' && tieneDiurno) diasConFijo.push(i);
    }

    if (diasConFijo.length > 0) {
        const nombres = diasConFijo.map(i => diasNombres[i]).join(', ');
        toastr.warning(
            `Tiene turnos fijos diurnos: ${nombres}. ` +
            `Si el día anterior se asigna turno nocturno, el trabajador no descansará.`,
            'Advertencia', { timeOut: 6000 }
        );
    }
}
</script>
```

---

## 5. Validación 2 — No fijo en domingo (bloqueante)

Los domingos están excluidos de los patrones fijos porque el builder los
gestiona con HR7 (mínimo 2 domingos libres). Documentado en validaciones
del backend y frontend de la sección anterior.

---

## 6. Validación 3 — Fijo diurno + nocturno día anterior (advertencia)

No bloqueante — es decisión del operador. El sistema advierte pero permite
guardar. Documentado en `detectarConflictoNoche()` de la sección anterior.

---

## 7. Resumen de validaciones

| # | Validación | Dónde | Tipo | Mensaje |
|---|---|---|---|---|
| V1 | max fijos ≤ ceil(horas/duracion_turno) | Frontend + Backend | Bloqueante | "Máximo N días fijos con Xh semanales" |
| V2 | No fijo en domingo | Frontend + Backend | Bloqueante | "Los domingos no pueden ser fijos" |
| V3 | Fijo diurno + posible noche anterior | Solo Frontend | Advertencia | "Posible conflicto con turno nocturno" |

---

## 8. Archivos a crear/modificar

| Archivo | Cambio |
|---|---|
| `app/utils.py` | Crear — función `calcular_horas_turno` compartida |
| `app/controllers/planificacion_bp.py` | Importar desde `utils.py`, eliminar función local |
| `app/controllers/trabajador_bp.py` | Agregar validaciones V1 y V2 + pasar `max_fijos` y `duracion_turno` al modal |
| `app/templates/modal-trabajador.html` | JS validaciones + indicador visual |

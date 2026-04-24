# Features rápidos — Gestión operativa del cuadrante

**Prioridad:** Alta — implementar antes de la demo con clientes
**Esfuerzo estimado:** 1 sprint (2 semanas)

---

## 1. Alerta de capacidad profunda (día/turno)

### Por qué el semáforo global no es suficiente

```
Ejemplo real que pasó en producción:

  Turnos necesarios: 120
  Turnos cubiertos:  134  ← global dice OK ✅
  Superávit:          14

  PERO:
  Domingo 5  turno T: necesita 1, disponible 0  ❌
  Domingo 12 turno T: necesita 1, disponible 0  ❌
  Domingo 26 turno N: necesita 1, disponible 0  ❌

El superávit de 14 está concentrado en días de semana.
El déficit está escondido en domingos específicos.
Un semáforo global nunca lo detectaría.
```

### Cuándo se dispara

```
1. Al registrar una ausencia nueva           → impacto inmediato
2. Al modificar o eliminar una ausencia      → recalcular
3. Al entrar a la pantalla de ausencias      → siempre visible
4. Al abrir el modal de "Nueva Planificación" → antes de generar
```

### Qué analiza (día × turno)

```python
# Para cada día del mes × cada turno:
#   ¿Cuántos trabajadores están disponibles ese día para ese turno?
#
# Un trabajador NO está disponible si:
#   → tiene ausencia ese día (vacaciones, licencia, etc.)
#   → es domingo y ya agotó sus 2 domingos libres mínimos
#   → tiene el turno bloqueado (turnos_permitidos, futuro)
#
# Si disponibles < dotacion_requerida → día/turno con problema

dias_con_problema = [
    {
        'fecha':      '05/05',
        'dia_semana': 'Dom',
        'turno':      'Tarde',
        'requerido':  1,
        'disponible': 0,
        'deficit':    1,
        'es_domingo': True,
    },
    ...
]
```

### Qué muestra el aviso en pantalla

```
🔴 3 combinaciones día/turno sin cobertura suficiente:

  Dom 05 mayo   Tarde    necesita 1 — disponible 0   falta 1
  Dom 12 mayo   Tarde    necesita 1 — disponible 0   falta 1
  Dom 26 mayo   Noche    necesita 1 — disponible 0   falta 1

  Causa: trabajadores han agotado los domingos laborables del mes.

  Opciones sugeridas:
  → Reducir dotación dominical en esos turnos
  → Agregar un trabajador disponible para domingos
  → Ajustar las ausencias del mes
```

### Por qué es un feature rápido

- No usa el solver — es aritmética pura
- Corre en < 100ms para 30 trabajadores
- Reutiliza datos que ya existen (ausencias, dotacion_diaria, domingos)
- Un solo endpoint que retorna JSON
- El semáforo en el frontend es CSS simple

---

## 2. Pantalla separada de Ausencias

### Problema actual

Las ausencias están dentro del mantenedor del trabajador. Para registrar
una ausencia hay que:

```
Hoy:
  Menú → Trabajadores → buscar → abrir modal → pestaña Ausencias → agregar
  (5 pasos, sin visibilidad global, sin alerta de impacto)

Ideal:
  Menú → Ausencias → Nueva Ausencia
  (1 paso, semáforo visible, alerta inmediata)
```

### Qué incluye la pantalla

```
┌─────────────────────────────────────────────────────────────┐
│  Gestión de Ausencias                    [+ Nueva Ausencia] │
├─────────────────────────────────────────────────────────────┤
│  Filtros: [Empresa ▼] [Mayo 2026 ▼] [Tipo ▼] [Trabajador]  │
├─────────────────────────────────────────────────────────────┤
│  Semáforo:  🔴 3 días/turno sin cobertura en domingos       │
│             Ver detalle ▼                                    │
├─────────────────────────────────────────────────────────────┤
│  Vista calendario:                                          │
│  Lun  Mar  Mié  Jue  Vie  Sáb  Dom                         │
│   1    2    3    4    5    6    7                            │
│              ████Ana-VAC████████                            │
│                        Pedro-LM                             │
├─────────────────────────────────────────────────────────────┤
│  Lista:                                                     │
│  Ana González    VAC   01/05–07/05  7 días  [✏️][🗑️]        │
│  Pedro Rojas     LM    05/05–15/05  11 días [✏️][🗑️]        │
└─────────────────────────────────────────────────────────────┘
```

### Modal "Nueva Ausencia"

```
[Trabajador *]  [selector con búsqueda]
[Tipo *]        [Vacaciones ▼]
[Desde *]       [01/05/2026]
[Hasta *]       [07/05/2026]
[Motivo]        [campo libre opcional]

→ Al completar las fechas, calcular y mostrar impacto:
  "Esta ausencia afecta 7 días hábiles.
   🟢 La dotación del mes se mantiene cubierta."
  o
  "⚠️ Esta ausencia genera déficit en Dom 12 turno Tarde."

[Cancelar]  [Guardar]
```

### Qué se queda en el mantenedor del trabajador

```
Mantenedor trabajador mantiene (sin cambios):
  ✅ Datos personales y contrato
  ✅ Patrones de turno por día de semana

Se agrega al mantenedor del trabajador:
  📋 Historial de ausencias (solo lectura, link a la pantalla de ausencias)
     "Ver historial de ausencias →"

Se mueve a pantalla separada:
  ✅ Crear / editar / eliminar ausencias
  ✅ Vista calendario del mes
  ✅ Alerta de impacto en dotación
```

---

## 3. ¿Sacar los patrones de turno del mantenedor del trabajador?

### Mi recomendación: NO sacarlos, pero agregar una vista global

**Por qué se quedan en el mantenedor:**

```
Los patrones son una característica permanente del trabajador.
"Pepito siempre los lunes trabaja turno M" es parte de su perfil,
como su RUT o sus horas de contrato.

Tiene sentido verlo y editarlo junto al trabajador porque:
  → Cuando contratas a alguien, defines su patrón en ese mismo momento
  → Si cambia de área, cambias su patrón en su ficha
  → El contexto es la persona, no el calendario
```

**Pero hay un problema real con la vista actual:**

```
El administrador no puede ver TODOS los patrones de la empresa juntos.
Para saber quién trabaja los lunes por la mañana, tiene que revisar
trabajador por trabajador.
```

**La solución: agregar una vista de patrones en la pantalla de planificación**

```
Antes de generar el cuadrante, mostrar un resumen:

  "Patrones fijos activos para Mayo 2026"

  Lunes:   Ana→M  Pedro→T  Felipe→M
  Martes:  Ana→M  Carlos→I
  Miércoles: Ana→M  Pedro→T
  ...
  Domingo: (ningún patrón — solver decide con restricción de 2 libres)

  ⚠️ 2 trabajadores sin patrón definido: Valentina, Diego
     El solver asignará sus turnos libremente.
```

---

## 4. Estructura de la nueva pantalla de ausencias

### Modelo de datos (sin cambios — ya existe)

```
TrabajadorAusencia ya tiene todo lo necesario:
  trabajador_id
  fecha_inicio
  fecha_fin
  motivo
  tipo_ausencia_id

No se necesita migración de BD para este feature.
```

### Blueprint nuevo

```python
# controllers/ausencia_bp.py

ausencia_bp = Blueprint('ausencia', __name__, url_prefix='/ausencias')

@ausencia_bp.route('/')
@login_required
def index():
    empresa_id = get_empresa_activa()
    mes  = int(request.args.get('mes',  date.today().month))
    anio = int(request.args.get('anio', date.today().year))

    ausencias  = TrabajadorAusencia.query\
        .join(Trabajador)\
        .filter(Trabajador.empresa_id == empresa_id)\
        .filter(...)  # filtrar por mes/año
        .all()

    capacidad  = calcular_capacidad_detallada(empresa_id, mes, anio)
    tipos      = TipoAusencia.query.filter_by(empresa_id=empresa_id, activo=True).all()

    return render_template('ausencias.html',
                           ausencias=ausencias,
                           capacidad=capacidad,
                           tipos=tipos,
                           mes=mes, anio=anio)


@ausencia_bp.route('/impacto', methods=['POST'])
@login_required
def calcular_impacto():
    """
    Endpoint AJAX: dado un trabajador y rango de fechas,
    calcular el impacto en la dotación ANTES de guardar.
    """
    empresa_id     = get_empresa_activa()
    trabajador_id  = int(request.json.get('trabajador_id'))
    fecha_inicio   = date.fromisoformat(request.json.get('fecha_inicio'))
    fecha_fin      = date.fromisoformat(request.json.get('fecha_fin'))
    mes            = fecha_inicio.month
    anio           = fecha_inicio.year
    dias           = (fecha_fin - fecha_inicio).days + 1

    resultado = calcular_capacidad_detallada(
        empresa_id=empresa_id,
        mes=mes, anio=anio,
        ausencias_nuevas=[{
            'trabajador_id': trabajador_id,
            'fecha_inicio':  fecha_inicio,
            'fecha_fin':     fecha_fin
        }]
    )
    return jsonify(resultado)


@ausencia_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    """Guarda la ausencia y retorna el estado de capacidad actualizado."""
    ...
```

### JavaScript — alerta en tiempo real

```javascript
// En modal de nueva ausencia:
// Cuando el usuario completa las fechas, calcular impacto sin guardar

$('#fecha_fin').on('change', function() {
    const trabajadorId = $('#trabajador_id').val();
    const fechaInicio  = $('#fecha_inicio').val();
    const fechaFin     = $(this).val();

    if (!trabajadorId || !fechaInicio || !fechaFin) return;

    $.ajax({
        url: '/ausencias/impacto',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            trabajador_id: trabajadorId,
            fecha_inicio:  fechaInicio,
            fecha_fin:     fechaFin
        }),
        success: function(res) {
            const $alerta = $('#alerta-impacto');
            if (res.estado === 'critico') {
                $alerta.removeClass('d-none alert-success alert-warning')
                       .addClass('alert-danger')
                       .html(`⚠️ ${res.mensaje}<br>
                              <small>${res.dias_con_problema.map(p =>
                                  `${p.dia_semana} ${p.fecha} — ${p.turno}: falta ${p.deficit}`
                              ).join('<br>')}</small>`);
            } else if (res.estado === 'atencion') {
                $alerta.removeClass('d-none alert-danger alert-success')
                       .addClass('alert-warning')
                       .html(`⚠️ ${res.mensaje}`);
            } else {
                $alerta.removeClass('d-none alert-danger alert-warning')
                       .addClass('alert-success')
                       .html(`✅ ${res.mensaje}`);
            }
        }
    });
});
```

---

## 5. Resumen de cambios al mantenedor del trabajador

### Lo que cambia

| Sección | Antes | Después |
|---|---|---|
| Ausencias | Crear/editar/eliminar aquí | Solo historial (lectura) + link |
| Patrones de turno | Crear/editar/eliminar aquí | Se mantiene aquí ✅ |
| Datos personales | Sin cambios | Sin cambios ✅ |
| Contrato/horas | Sin cambios | Sin cambios ✅ |

### Lo que se agrega al mantenedor

```
Sección "Historial de ausencias" (solo lectura):
  Mayo 2026:  VAC  01/05 → 07/05
  Marzo 2026: LM   15/03 → 20/03
  [Ver todas las ausencias →]  ← link a la pantalla separada
```

---

## 6. Plan de implementación (1 sprint)

```
Semana 1:
  Día 1-2:  calcular_capacidad_detallada() + tests
  Día 3:    Endpoint /ausencias/impacto (AJAX)
  Día 4-5:  Template ausencias.html + modal nueva ausencia

Semana 2:
  Día 1-2:  Semáforo visual en pantalla de ausencias
  Día 3:    JavaScript de alerta en tiempo real (on change fechas)
  Día 4:    Modificar mantenedor trabajador (historial read-only)
  Día 5:    Vista de patrones en pantalla de planificación
```

### Dependencias

```
No requiere:
  ❌ Migración de BD nueva
  ❌ Cambios en el builder
  ❌ Autenticación implementada (puede ir en paralelo)

Requiere:
  ✅ TipoAusencia con datos en BD
  ✅ TrabajadorAusencia funcionando (ya existe)
  ✅ Turno.dotacion_diaria configurado por empresa
```

---

## 7. Por qué estos features venden el sistema

```
Feature                      Lo que ve el cliente en la demo
────────────────────────────────────────────────────────────────
Semáforo global              "Verde / Rojo — capacidad del mes"
                             Simple, visual, instantáneo

Alerta día/turno             "Registras una vacación y aparece:
                              Dom 12 turno T sin cobertura"
                             Wow inmediato — el sistema sabe más que tú

Vista calendario ausencias   Todos los trabajadores, todos los días,
                             en una sola pantalla
                             Profesional, no es una planilla Excel

Alerta antes de guardar      Sin haber guardado, ya sabes el impacto
                             Proactivo — no reactivo
```

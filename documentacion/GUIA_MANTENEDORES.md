# Guía: Cómo Crear un Nuevo Mantenedor (CRUD)

Este documento define el patrón estándar para crear un mantenedor con CRUD completo en SGT 2.1.
Está basado en la implementación de **Regiones** como caso de referencia.

---

## Estructura de archivos involucrados

```
app/
├── controllers/
│   └── {entidad}_bp.py            ← Rutas y lógica del mantenedor
├── models/
│   └── core.py / business.py      ← Clase SQLAlchemy ya definida
├── templates/
│   ├── {entidad}s.html            ← Vista principal con tabla
│   ├── modal-{entidad}.html       ← Formulario del modal
│   └── partials/
│       └── {entidad}_rows.html    ← Solo el <tbody> para HTMX refresh
└── __init__.py                    ← Registro del blueprint
```

---

## Paso 1: Verificar el Modelo en `models/`

Confirmar que la entidad tiene su clase SQLAlchemy en el archivo correspondiente:
- Entidades base (Región, Comuna, Feriado) → `models/core.py`
- Entidades de negocio (Empresa, Trabajador, Turno, etc.) → `models/business.py`
- Entidades de autenticación (Rol, Menú, Usuario) → `models/auth.py`

### Agregar índices al modelo (Optimización de BD)

Toda entidad debe declarar sus índices en `__table_args__` para que SQLAlchemy los cree automáticamente:

```python
class MiEntidad(db.Model):
    __tablename__ = 'mi_entidad'
    __table_args__ = (
        db.Index('ix_mi_entidad_activo',    'activo'),      # siempre
        db.Index('ix_mi_entidad_empresa_id','empresa_id'),  # si tiene FK a empresa
        # agregar índice por cada columna de filtro frecuente
    )
    id     = db.Column(db.Integer, primary_key=True)
    activo = db.Column(db.Boolean, default=True)
    ...
```

> **Regla:** Toda columna usada en `WHERE`, `.filter_by()` o `.order_by()` frecuente debe tener índice.
> También agregar el índice equivalente en `proyecto.sql` con `CREATE INDEX IF NOT EXISTS`.

---

## Paso 2: Crear el Blueprint `app/controllers/{entidad}_bp.py`

### Patrón con 5 rutas (4 obligatorias + 1 HTMX partial):

```python
from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.core import MiEntidad  # importar el modelo correcto

entidad_bp = Blueprint('entidad', __name__, url_prefix='/entidades')


@entidad_bp.route('/')
def index():
    """Página completa: renderiza tabla con todos los registros."""
    registros = MiEntidad.query.order_by(MiEntidad.campo_orden).all()
    return render_template('entidades.html', registros=registros)


@entidad_bp.route('/tabla')
def tabla():
    """Solo el <tbody> para HTMX partial refresh (no recarga la página)."""
    registros = MiEntidad.query.order_by(MiEntidad.campo_orden).all()
    return render_template('partials/entidad_rows.html', registros=registros)


@entidad_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal YA relleno con datos de la BD."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = MiEntidad.query.get_or_404(int(registro_id))
    return render_template('modal-entidad.html', modo=modo, registro=registro)


@entidad_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza en PostgreSQL."""
    registro_id = request.form.get('id', '').strip()
    campo1 = request.form.get('campo1', '').strip()

    if not campo1:
        return jsonify({'ok': False, 'msg': 'Campo1 es obligatorio.'}), 400

    if registro_id and registro_id != '0':
        registro = MiEntidad.query.get_or_404(int(registro_id))
        registro.campo1 = campo1
        msg = f'"{campo1}" actualizado con éxito.'
    else:
        registro = MiEntidad(campo1=campo1)
        db.session.add(registro)
        msg = f'"{campo1}" creado con éxito.'

    db.session.commit()
    return jsonify({'ok': True, 'msg': msg})


@entidad_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Eliminación lógica (activo = False)."""
    registro_id = request.form.get('id', '').strip()
    registro = MiEntidad.query.get_or_404(int(registro_id))
    registro.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'"{registro.campo1}" desactivado.'})
```

---

## Paso 3: Registrar el Blueprint en `app/__init__.py`

```python
def create_app():
    ...
    from .controllers.entidad_bp import entidad_bp
    app.register_blueprint(entidad_bp)
    ...
```

---

## Paso 4: Partial HTMX `templates/partials/{entidad}_rows.html`

Contiene **solo las filas** `<tr>` del tbody. Este archivo es el que HTMX usará para refrescar la tabla sin recargar la página.

```html
{% for r in registros %}
<tr>
    <td>{{ r.campo1 }}</td>
    <td>
        <span class="badge bg-{{ 'success' if r.activo else 'danger' }}-subtle
                         text-{{ 'success' if r.activo else 'danger' }}">
            {{ 'Activo' if r.activo else 'Inactivo' }}
        </span>
    </td>
    <td class="text-center">
        <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-info"
                onclick="Modal('Visualizar', {{ r.id }}, '{{ url_for('entidad.modal') }}')">
                <i class="fa fa-eye"></i>
            </button>
            <button class="btn btn-outline-warning"
                onclick="Modal('Editar', {{ r.id }}, '{{ url_for('entidad.modal') }}')">
                <i class="fa fa-edit"></i>
            </button>
            <button class="btn btn-outline-danger"
                onclick="eliminarEntidad({{ r.id }}, '{{ r.campo1 }}')">
                <i class="fa fa-ban"></i>
            </button>
        </div>
    </td>
</tr>
{% else %}
<tr><td colspan="3" class="text-center text-muted">Sin registros.</td></tr>
{% endfor %}
```

---

## Paso 5: Template principal `{entidad}s.html`

### Reglas críticas:
1. El `<tbody>` tiene `id="tbody-entidad"` para que HTMX sepa dónde inyectar.
2. El tbody usa `{% include 'partials/entidad_rows.html' %}` — carga inicial desde servidor.
3. Tras Guardar/Eliminar, se llama a `refreshTablaEntidad()` — **no a `location.reload()`**.
4. `dtEntidad` se destruye y reinicializa para que DataTable vea los nuevos datos.

```html
{% extends "layout.html" %}
{% block actions %}
<button class="btn btn-primary" onclick="Modal('Agregar', 0, '{{ url_for('entidad.modal') }}')">
    <i class="fa fa-plus me-1"></i> Agregar
</button>
{% endblock %}

{% block content %}
<table id="tabla_entidad" class="table table-hover dt-responsive nowrap w-100">
    <thead class="table-light">
        <tr><th>Campo 1</th><th>Estado</th><th class="text-center">Acciones</th></tr>
    </thead>
    <tbody id="tbody-entidad">
        {% include 'partials/entidad_rows.html' %}
    </tbody>
</table>
{% endblock %}

{% block scripts %}
<script>
let dtEntidad;

$(document).ready(function() {
    dtEntidad = $('#tabla_entidad').DataTable({
        responsive: true,
        language: { url: '/static/i18n/es-ES.json' }
    });
});

// Refresh parcial: solo actualiza el tbody via HTMX, sin recargar la página
function refreshTablaEntidad() {
    htmx.ajax('GET', "{{ url_for('entidad.tabla') }}", {
        target: '#tbody-entidad',
        swap: 'innerHTML'
    }).then(() => {
        dtEntidad.destroy();
        dtEntidad = $('#tabla_entidad').DataTable({
            responsive: true,
            language: { url: '/static/i18n/es-ES.json' }
        });
    });
}

function eliminarEntidad(id, nombre) {
    Swal.fire({
        title: '¿Desactivar?',
        text: `"${nombre}" quedará inactivo.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, desactivar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#e74c3c'
    }).then(result => {
        if (!result.isConfirmed) return;
        $('#fondo').fadeIn();
        $.post("{{ url_for('entidad.eliminar') }}", { id })
            .done(res => {
                if (res.ok) { toastr.success(res.msg); refreshTablaEntidad(); }
                else toastr.error(res.msg);
            })
            .always(() => $('#fondo').fadeOut());
    });
}
</script>
{% endblock %}
```

---

## Paso 6: Modal `modal-{entidad}.html`

### Reglas críticas:
1. El título viene del modo en Jinja (sin JS para cambiarlo).
2. `value` de los campos usa Jinja: `{{ registro.campo if registro else '' }}`.
3. Botón Guardar oculto en modo `Visualizar` via Jinja (no con JS).
4. Tras guardar llama a `refreshTablaEntidad()` — **no a `location.reload()`**.
5. `CerrarModal()` es la función global del layout.

```html
<div class="modal-header bg-primary text-white">
    <h5 class="modal-title fw-bold">
        {% if modo == 'Agregar' %}Nueva Entidad
        {% elif modo == 'Editar' %}Editar Entidad
        {% else %}Detalle de Entidad
        {% endif %}
    </h5>
    <button type="button" class="btn-close btn-close-white" onclick="CerrarModal()"></button>
</div>

<div class="modal-body p-4">
    <form id="form_entidad">
        <input type="hidden" id="id_entidad" value="{{ registro.id if registro else 0 }}">
        <div class="row g-3">
            <div class="col-md-12">
                <label class="form-label small fw-bold text-muted"><code>(*)</code> Campo 1</label>
                <input type="text"
                       class="form-control {% if modo == 'Visualizar' %}bg-light{% endif %}"
                       id="campo1_entidad"
                       value="{{ registro.campo1 if registro else '' }}"
                       {% if modo == 'Visualizar' %}readonly{% endif %}>
            </div>
        </div>
    </form>
</div>

<div class="modal-footer bg-light border-top-0">
    <button type="button" class="btn btn-secondary" onclick="CerrarModal()">Cancelar</button>
    {% if modo != 'Visualizar' %}
    <button type="button" class="btn btn-primary px-4" onclick="guardarEntidad()">
        <i class="fa fa-save me-1"></i> Guardar
    </button>
    {% endif %}
</div>

<script>
function guardarEntidad() {
    const id     = $('#id_entidad').val();
    const campo1 = $('#campo1_entidad').val().trim();

    if (!campo1) { toastr.warning('Campo1 es obligatorio.'); return; }

    $('#fondo').fadeIn();
    $.post("{{ url_for('entidad.guardar') }}", { id, campo1 })
        .done(res => {
            if (res.ok) {
                toastr.success(res.msg);
                CerrarModal();
                refreshTablaEntidad(); // ← HTMX, no location.reload()
            } else {
                toastr.error(res.msg);
                $('#fondo').fadeOut();
            }
        })
        .fail(() => { toastr.error('Error de servidor.'); $('#fondo').fadeOut(); });
}
</script>
```

---

## Paso 7: Actualizar el sidebar en `layout.html`

```html
<!-- Cambiar 'main.entidades' por 'entidad.index' -->
href="{{ url_for('entidad.index') }}"
hx-get="{{ url_for('entidad.index') }}"
```

---

## Resumen del flujo completo

### Apertura de modal (sin reload)
```
Click "Editar" → Modal(modo, id, url)
    → POST /entidad/modal
    → Backend: BD → Jinja → HTML relleno
    → layout.js: inserta en #modal_contenido → .modal('show')
```

### Guardar / Eliminar (sin reload)
```
Click "Guardar" → $.post(/entidad/guardar)
    → Backend: UPDATE/INSERT en PostgreSQL → jsonify({ok: True})
    → JS: CerrarModal() + refreshTablaEntidad()
        → htmx.ajax GET /entidad/tabla
        → Backend: SELECT → Jinja → solo <tbody>
        → HTMX: reemplaza innerHTML de #tbody-entidad
        → JS: destroy() + reinit DataTable
```

**Nunca usar `location.reload()`** — siempre HTMX partial refresh.

---

## Errores comunes a evitar

| Error | Corrección |
|---|---|
| Usar `$('#modalPrincipal')` | Usar la función global `Modal()` del layout |
| Usar `$('#modalContent')` | El contenedor correcto es `#modal_contenido .modal-content` |
| `readonly`/`disabled` con JS | Usar Jinja: `{% if modo == 'Visualizar' %}readonly{% endif %}` |
| `location.reload()` tras guardar | Usar `refreshTablaEntidad()` con HTMX |
| Quitar ruta del `main_bp` sin actualizar sidebar | Siempre actualizar `layout.html` al mismo tiempo |
| Olvidar registrar el blueprint en `__init__.py` | Siempre terminar con este paso |
| Olvidar crear `partials/{entidad}_rows.html` | Necesario para que HTMX pueda refrescar el tbody |

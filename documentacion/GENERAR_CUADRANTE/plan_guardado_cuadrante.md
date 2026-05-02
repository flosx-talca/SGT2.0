# PLAN DE IMPLEMENTACIÓN: Guardado de Cuadrante y Auditoría — SGT 2.1

> **Estado**: Pendiente de implementación
> **Stack**: Flask + Flask-SQLAlchemy 3.1.1 + PostgreSQL + HTMX + DataTables
> **Visación requerida**: Toda implementación debe ser aprobada por el usuario responsable.

---

## 1. RESUMEN FUNCIONAL

Este módulo cubre:

1. **Persistir el cuadrante generado** en BD con estructura multiempresa/multiservicio.
2. **Renombrar "Publicar" → "Guardar Cuadrante"** en `planificacion.html`.
3. **Asignaciones manuales post-guardado**: el tooltip existente se convierte en selector de turno. Cada cambio queda registrado con el usuario logueado.
4. **Auditoría legal**: diferenciación entre asignaciones del Solver (`origen=solver`) y modificaciones manuales (`origen=manual`).
5. **Dashboard "Últimas Planificaciones"**: DataTable con el mismo patrón de `trabajadores.html`.

---

## 2. ESTRUCTURA DE TABLAS

### 2.1 `cuadrante_cabecera`

```sql
CREATE TABLE cuadrante_cabecera (
    id                    SERIAL PRIMARY KEY,
    empresa_id            INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id           INTEGER NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    servicio_id           INTEGER REFERENCES servicio(id) ON DELETE SET NULL,
    mes                   SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio                  SMALLINT NOT NULL CHECK (anio >= 2024),
    estado                VARCHAR(20) NOT NULL DEFAULT 'guardado'
                          CHECK (estado IN ('guardado', 'cerrado')),
    generado_por_user_id  INTEGER REFERENCES user(id) ON DELETE SET NULL,
    generado_en           TIMESTAMP DEFAULT NOW(),
    guardado_por_user_id  INTEGER REFERENCES user(id) ON DELETE SET NULL,
    guardado_en           TIMESTAMP,
    creado_en             TIMESTAMP DEFAULT NOW(),
    UNIQUE (sucursal_id, servicio_id, mes, anio)
);

CREATE INDEX idx_cab_empresa ON cuadrante_cabecera(empresa_id, anio, mes);
CREATE INDEX idx_cab_sucursal ON cuadrante_cabecera(sucursal_id, anio, mes);
```

### 2.2 `cuadrante_asignacion`

```sql
CREATE TABLE cuadrante_asignacion (
    id                       SERIAL PRIMARY KEY,
    cabecera_id              INTEGER NOT NULL
                             REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    trabajador_id            INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    fecha                    DATE NOT NULL,
    turno_id                 INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    es_libre                 BOOLEAN NOT NULL DEFAULT FALSE,
    horas_asignadas          NUMERIC(4,2) DEFAULT 0,

    -- Auditoría legal: origen de la asignación
    origen                   VARCHAR(10) NOT NULL DEFAULT 'solver'
                             CHECK (origen IN ('solver', 'manual')),
    modificado_por_user_id   INTEGER REFERENCES user(id) ON DELETE SET NULL,
    modificado_en            TIMESTAMP,

    -- Flags de clasificación del día (para trazabilidad legal)
    es_feriado               BOOLEAN DEFAULT FALSE,
    es_domingo               BOOLEAN DEFAULT FALSE,
    es_irrenunciable         BOOLEAN DEFAULT FALSE,
    es_feriado_regional      BOOLEAN DEFAULT FALSE,
    tipo_dia                 VARCHAR(30) DEFAULT 'normal',
    -- tipo_dia: normal | domingo | feriado | feriado-irrenunciable |
    --           feriado-regional | domingo-feriado | domingo-irrenunciable

    UNIQUE (cabecera_id, trabajador_id, fecha)
);

CREATE INDEX idx_asig_cabecera ON cuadrante_asignacion(cabecera_id);
CREATE INDEX idx_asig_trabajador ON cuadrante_asignacion(trabajador_id, fecha);
CREATE INDEX idx_asig_origen ON cuadrante_asignacion(origen);
```

### 2.3 `cuadrante_auditoria`

```sql
CREATE TABLE cuadrante_auditoria (
    id                  SERIAL PRIMARY KEY,
    asignacion_id       INTEGER NOT NULL
                        REFERENCES cuadrante_asignacion(id) ON DELETE CASCADE,
    cabecera_id         INTEGER NOT NULL
                        REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    user_id             INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    fecha_cambio        TIMESTAMP NOT NULL DEFAULT NOW(),
    turno_anterior_id   INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    turno_nuevo_id      INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    era_libre_antes     BOOLEAN DEFAULT FALSE,
    es_libre_ahora      BOOLEAN DEFAULT FALSE,
    ip_address          VARCHAR(45),
    motivo              VARCHAR(255)
);

CREATE INDEX idx_aud_asignacion ON cuadrante_auditoria(asignacion_id);
CREATE INDEX idx_aud_user ON cuadrante_auditoria(user_id, fecha_cambio DESC);
CREATE INDEX idx_aud_cabecera ON cuadrante_auditoria(cabecera_id, fecha_cambio DESC);
```

---

## 3. MODELOS SQLAlchemy (`app/models/scheduling.py` — archivo nuevo)

```python
from datetime import datetime
from app import db

class CuadranteCabecera(db.Model):
    __tablename__ = 'cuadrante_cabecera'

    id                   = db.Column(db.Integer, primary_key=True)
    empresa_id           = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    sucursal_id          = db.Column(db.Integer, db.ForeignKey('sucursal.id', ondelete='CASCADE'), nullable=False)
    servicio_id          = db.Column(db.Integer, db.ForeignKey('servicio.id', ondelete='SET NULL'), nullable=True)
    mes                  = db.Column(db.SmallInteger, nullable=False)
    anio                 = db.Column(db.SmallInteger, nullable=False)
    estado               = db.Column(db.String(20), default='guardado')
    generado_por_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    generado_en          = db.Column(db.DateTime, default=datetime.utcnow)
    guardado_por_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    guardado_en          = db.Column(db.DateTime)
    creado_en            = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    asignaciones = db.relationship('CuadranteAsignacion', backref='cabecera',
                                   lazy='dynamic', cascade='all, delete-orphan')
    empresa      = db.relationship('Empresa', foreign_keys=[empresa_id])
    sucursal     = db.relationship('Sucursal', foreign_keys=[sucursal_id])

    @property
    def periodo(self):
        meses = ['Ene','Feb','Mar','Abr','May','Jun',
                 'Jul','Ago','Sep','Oct','Nov','Dic']
        return f"{meses[self.mes - 1]} {self.anio}"

    @property
    def total_asignaciones(self):
        from sqlalchemy import select, func
        from app import db as _db
        return _db.session.execute(
            select(func.count()).select_from(CuadranteAsignacion)
            .where(CuadranteAsignacion.cabecera_id == self.id)
        ).scalar()

    @property
    def total_manuales(self):
        from sqlalchemy import select, func
        from app import db as _db
        return _db.session.execute(
            select(func.count()).select_from(CuadranteAsignacion)
            .where(CuadranteAsignacion.cabecera_id == self.id,
                   CuadranteAsignacion.origen == 'manual')
        ).scalar()


class CuadranteAsignacion(db.Model):
    __tablename__ = 'cuadrante_asignacion'

    id                     = db.Column(db.Integer, primary_key=True)
    cabecera_id            = db.Column(db.Integer, db.ForeignKey('cuadrante_cabecera.id', ondelete='CASCADE'), nullable=False)
    trabajador_id          = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    fecha                  = db.Column(db.Date, nullable=False)
    turno_id               = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    es_libre               = db.Column(db.Boolean, default=False)
    horas_asignadas        = db.Column(db.Numeric(4, 2), default=0)
    origen                 = db.Column(db.String(10), default='solver')
    modificado_por_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    modificado_en          = db.Column(db.DateTime)
    es_feriado             = db.Column(db.Boolean, default=False)
    es_domingo             = db.Column(db.Boolean, default=False)
    es_irrenunciable       = db.Column(db.Boolean, default=False)
    es_feriado_regional    = db.Column(db.Boolean, default=False)
    tipo_dia               = db.Column(db.String(30), default='normal')

    # Relaciones
    turno      = db.relationship('Turno', foreign_keys=[turno_id])
    trabajador = db.relationship('Trabajador', foreign_keys=[trabajador_id])

    @property
    def es_manual(self):
        return self.origen == 'manual'


class CuadranteAuditoria(db.Model):
    __tablename__ = 'cuadrante_auditoria'

    id                = db.Column(db.Integer, primary_key=True)
    asignacion_id     = db.Column(db.Integer, db.ForeignKey('cuadrante_asignacion.id', ondelete='CASCADE'), nullable=False)
    cabecera_id       = db.Column(db.Integer, db.ForeignKey('cuadrante_cabecera.id', ondelete='CASCADE'), nullable=False)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    fecha_cambio      = db.Column(db.DateTime, default=datetime.utcnow)
    turno_anterior_id = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    turno_nuevo_id    = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    era_libre_antes   = db.Column(db.Boolean, default=False)
    es_libre_ahora    = db.Column(db.Boolean, default=False)
    ip_address        = db.Column(db.String(45))
    motivo            = db.Column(db.String(255))
```

---

## 4. SERVICIO DE GUARDADO (`app/services/cuadrante_service.py` — archivo nuevo)

```python
from datetime import datetime
from sqlalchemy import select
from flask_login import current_user
from app import db
from app.models.scheduling import CuadranteCabecera, CuadranteAsignacion, CuadranteAuditoria
from app.models.core import Feriado
from calendar import monthrange

def clasificar_dia(fecha, feriados_dict: dict) -> dict:
    feriado = feriados_dict.get(fecha)
    es_dom  = (fecha.weekday() == 6)
    es_fer  = feriado is not None and feriado.activo
    es_irr  = feriado.es_irrenunciable if feriado else False
    es_reg  = feriado.es_regional if feriado else False

    if es_irr and es_dom:   tipo_dia = 'domingo-irrenunciable'
    elif es_irr:            tipo_dia = 'feriado-irrenunciable'
    elif es_fer and es_dom: tipo_dia = 'domingo-feriado'
    elif es_reg:            tipo_dia = 'feriado-regional'
    elif es_fer:            tipo_dia = 'feriado'
    elif es_dom:            tipo_dia = 'domingo'
    else:                   tipo_dia = 'normal'

    return {
        'es_feriado': es_fer, 'es_domingo': es_dom,
        'es_irrenunciable': es_irr, 'es_feriado_regional': es_reg,
        'tipo_dia': tipo_dia
    }


def guardar_cuadrante(empresa_id, sucursal_id, servicio_id,
                      mes, anio, asignaciones: list) -> CuadranteCabecera:
    """
    Persiste el cuadrante generado por el Solver.
    asignaciones: lista de dicts con keys:
        trabajador_id, fecha, turno_id, es_libre, horas_asignadas
    """
    # Precargar feriados del mes
    from datetime import date
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, monthrange(anio, mes)[1])
    feriados = db.session.execute(
        select(Feriado).where(
            Feriado.fecha.between(primer_dia, ultimo_dia),
            Feriado.activo == True
        )
    ).scalars().all()
    feriados_dict = {f.fecha: f for f in feriados}

    # Si ya existe un cuadrante para este período, eliminarlo (reemplazar)
    existente = db.session.execute(
        select(CuadranteCabecera).where(
            CuadranteCabecera.sucursal_id == sucursal_id,
            CuadranteCabecera.servicio_id == servicio_id,
            CuadranteCabecera.mes == mes,
            CuadranteCabecera.anio == anio
        )
    ).scalar_one_or_none()

    if existente:
        db.session.delete(existente)
        db.session.flush()

    # Crear cabecera
    cabecera = CuadranteCabecera(
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        servicio_id=servicio_id,
        mes=mes, anio=anio,
        estado='guardado',
        generado_por_user_id=current_user.id,
        guardado_por_user_id=current_user.id,
        guardado_en=datetime.utcnow()
    )
    db.session.add(cabecera)
    db.session.flush()  # obtener cabecera.id

    # Insertar asignaciones
    for a in asignaciones:
        flags = clasificar_dia(a['fecha'], feriados_dict)
        db.session.add(CuadranteAsignacion(
            cabecera_id=cabecera.id,
            trabajador_id=a['trabajador_id'],
            fecha=a['fecha'],
            turno_id=a.get('turno_id'),
            es_libre=a.get('es_libre', False),
            horas_asignadas=a.get('horas_asignadas', 0),
            origen='solver',
            **flags
        ))

    db.session.commit()
    return cabecera


def editar_asignacion_manual(asignacion_id: int, turno_nuevo_id,
                              es_libre: bool, motivo: str,
                              ip: str) -> CuadranteAsignacion:
    """
    Modifica una asignación post-guardado.
    Registra el cambio en cuadrante_auditoria con el usuario logueado.
    """
    asig = db.session.execute(
        select(CuadranteAsignacion).where(CuadranteAsignacion.id == asignacion_id)
    ).scalar_one_or_none()

    if not asig:
        raise ValueError(f"Asignación {asignacion_id} no encontrada")

    # Registrar auditoría ANTES de modificar
    db.session.add(CuadranteAuditoria(
        asignacion_id=asig.id,
        cabecera_id=asig.cabecera_id,
        user_id=current_user.id,
        turno_anterior_id=asig.turno_id,
        turno_nuevo_id=turno_nuevo_id,
        era_libre_antes=asig.es_libre,
        es_libre_ahora=es_libre,
        ip_address=ip,
        motivo=motivo
    ))

    # Actualizar asignación
    asig.turno_id               = turno_nuevo_id
    asig.es_libre               = es_libre
    asig.origen                 = 'manual'
    asig.modificado_por_user_id = current_user.id
    asig.modificado_en          = datetime.utcnow()

    db.session.commit()
    return asig
```

---

## 5. ENDPOINTS (`app/controllers/cuadrante_bp.py` — archivo nuevo)

```python
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import select, desc
from app import db
from app.models.scheduling import CuadranteCabecera, CuadranteAsignacion
from app.services.cuadrante_service import guardar_cuadrante, editar_asignacion_manual

cuadrante_bp = Blueprint('cuadrante', __name__, url_prefix='/cuadrante')


@cuadrante_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    """Guarda el cuadrante generado por el Solver."""
    data = request.get_json()
    cabecera = guardar_cuadrante(
        empresa_id=data['empresa_id'],
        sucursal_id=data['sucursal_id'],
        servicio_id=data.get('servicio_id'),
        mes=data['mes'],
        anio=data['anio'],
        asignaciones=data['asignaciones']
    )
    return jsonify({"ok": True, "cabecera_id": cabecera.id})


@cuadrante_bp.route('/asignacion/<int:asig_id>', methods=['PUT'])
@login_required
def editar_asignacion(asig_id):
    """Modifica una asignación manualmente post-guardado."""
    data   = request.get_json()
    ip     = request.headers.get('X-Forwarded-For', request.remote_addr)
    asig   = editar_asignacion_manual(
        asignacion_id=asig_id,
        turno_nuevo_id=data.get('turno_id'),
        es_libre=data.get('es_libre', False),
        motivo=data.get('motivo', ''),
        ip=ip
    )
    return jsonify({
        "ok": True,
        "asignacion_id": asig.id,
        "origen": asig.origen,
        "turno_id": asig.turno_id,
        "es_libre": asig.es_libre
    })


@cuadrante_bp.route('/lista', methods=['GET'])
@login_required
def lista():
    """Retorna las últimas planificaciones para el DataTable del dashboard."""
    cabeceras = db.session.execute(
        select(CuadranteCabecera)
        .order_by(desc(CuadranteCabecera.guardado_en))
        .limit(50)
    ).scalars().all()

    return render_template(
        'cuadrante/lista_partial.html',
        cabeceras=cabeceras
    )
```

---

## 6. CAMBIOS EN `planificacion.html`

### 6.1 Renombrar botón

```html
<!-- ANTES -->
<button id="btn-publicar" class="btn btn-primary">
    <i class="fas fa-upload"></i> Publicar
</button>

<!-- DESPUÉS -->
<button id="btn-guardar-cuadrante" class="btn btn-success">
    <i class="fas fa-save"></i> Guardar Cuadrante
</button>
```

### 6.2 JavaScript: enviar cuadrante al backend

```javascript
document.getElementById('btn-guardar-cuadrante').addEventListener('click', () => {
    const asignaciones = recolectarAsignaciones(); // función que lee el cuadrante actual

    fetch('/cuadrante/guardar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            empresa_id:   window.EMPRESA_ID,
            sucursal_id:  window.SUCURSAL_ID,
            servicio_id:  window.SERVICIO_ID,
            mes:          window.MES,
            anio:         window.ANIO,
            asignaciones: asignaciones
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            window.CABECERA_ID = data.cabecera_id;
            activarModoEdicion(); // habilita tooltip como selector
            mostrarToast('Cuadrante guardado correctamente', 'success');
        }
    });
});
```

### 6.3 Tooltip → selector manual (post-guardado)

```javascript
function activarModoEdicion() {
    document.querySelectorAll('.celda-turno').forEach(celda => {
        celda.addEventListener('click', abrirSelectorTurno);
    });
}

function abrirSelectorTurno(event) {
    const celda       = event.currentTarget;
    const asigId      = celda.dataset.asignacionId;
    const turnoActual = celda.dataset.turnoId;

    // Construir select con turnos disponibles de la empresa
    const select = document.createElement('select');
    select.className = 'form-select form-select-sm';
    TURNOS_EMPRESA.forEach(t => {
        const opt = new Option(t.nombre, t.id, false, t.id == turnoActual);
        select.appendChild(opt);
    });

    // Opción de día libre
    select.insertBefore(new Option('Día Libre', '', false, !turnoActual), select.firstChild);

    select.addEventListener('change', () => guardarCambioManual(asigId, select.value, celda));
    celda.innerHTML = '';
    celda.appendChild(select);
    select.focus();
}

function guardarCambioManual(asigId, turnoNuevoId, celda) {
    fetch(`/cuadrante/asignacion/${asigId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            turno_id: turnoNuevoId || null,
            es_libre: !turnoNuevoId
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            // Actualizar celda visualmente
            celda.dataset.turnoId    = data.turno_id || '';
            celda.dataset.origen     = 'manual';
            const nombreTurno = TURNOS_MAP[data.turno_id] || 'Libre';
            celda.innerHTML = `${nombreTurno} <span title="Modificado manualmente">✏️</span>`;
        }
    });
}
```

---

## 7. DASHBOARD — "Últimas Planificaciones"

### Template parcial (`app/templates/cuadrante/lista_partial.html`)

Sigue el mismo patrón de `trabajadores.html`:

```html
{% extends "_partial.html" if is_htmx else "layout.html" %}
{% block title %}Últimas Planificaciones{% endblock %}

{% block content %}
<div class="card">
  <div class="card-body">
    <table id="tbl-planificaciones" class="table table-hover dt-table">
      <thead>
        <tr>
          <th>Empresa / Sucursal</th>
          <th>Servicio</th>
          <th>Período</th>
          <th>Estado</th>
          <th>Asig. Manuales</th>
          <th>Guardado por</th>
          <th>Fecha</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {% for c in cabeceras %}
        <tr>
          <td>{{ c.empresa.nombre }}<br>
              <small class="text-muted">{{ c.sucursal.nombre }}</small></td>
          <td>{{ c.servicio.nombre if c.servicio else '—' }}</td>
          <td>{{ c.periodo }}</td>
          <td>
            <span class="badge bg-{{ 'success' if c.estado == 'guardado' else 'secondary' }}">
              {{ c.estado|capitalize }}
            </span>
          </td>
          <td>
            {% if c.total_manuales > 0 %}
              <span class="badge bg-warning text-dark">✏️ {{ c.total_manuales }}</span>
            {% else %}
              <span class="text-muted">—</span>
            {% endif %}
          </td>
          <td>{{ c.guardado_por.nombre if c.guardado_por else '—' }}</td>
          <td>{{ c.guardado_en.strftime('%d/%m/%Y %H:%M') if c.guardado_en else '—' }}</td>
          <td>
            <a href="/planificacion/ver/{{ c.id }}"
               class="btn btn-sm btn-outline-primary">
               <i class="fas fa-eye"></i>
            </a>
            <a href="/planificacion/editar/{{ c.id }}"
               class="btn btn-sm btn-outline-warning">
               <i class="fas fa-edit"></i>
            </a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

---

## 8. ORDEN DE IMPLEMENTACIÓN

| Paso | Archivo | Acción |
|---|---|---|
| 1 | SQL + `app/models/scheduling.py` | Crear tablas y modelos |
| 2 | `app/services/cuadrante_service.py` | Crear servicio guardar + editar |
| 3 | `app/controllers/cuadrante_bp.py` | Crear blueprint con 3 endpoints |
| 4 | `app/__init__.py` | Registrar `cuadrante_bp` |
| 5 | `planificacion.html` | Renombrar botón + JS guardar + selector manual |
| 6 | `app/templates/cuadrante/lista_partial.html` | DataTable últimas planificaciones |
| 7 | `app/templates/dashboard.html` | Integrar la sección con HTMX |

---

## 9. TESTS DE ACEPTACIÓN

```
[TEST-CAUD-01] Guardar cuadrante → crea 1 cabecera + N asignaciones con origen=solver
[TEST-CAUD-02] Guardar el mismo período dos veces → reemplaza el anterior (no duplica)
[TEST-CAUD-03] Editar celda manualmente → origen cambia a manual, auditoría registra user+ip
[TEST-CAUD-04] Editar celda → celda muestra ✏️ en la visualización
[TEST-CAUD-05] Dashboard → DataTable muestra columna "Asig. Manuales" con badge ✏️
[TEST-CAUD-06] Auditoría → turno_anterior_id y turno_nuevo_id quedan registrados correctamente
[TEST-CAUD-07] Multiempresa → cuadrantes de empresas distintas no se mezclan en el listado
```

---

> **Recordatorio**: Toda implementación debe ser visada y aprobada por el usuario
> antes de ser confirmada en el repositorio.

# PROMPT PARA ANTIGRAVITY — Guardado de Cuadrante y Auditoría SGT 2.1

> Adjunta este archivo junto con `plan_guardado_cuadrante.md` como contexto.
> Lee el plan completo antes de comenzar.
> Aplica los cambios en el orden indicado.
> NO implementes el siguiente paso sin mostrarme el diff y esperar mi aprobación.

---

## STACK TÉCNICO

- **Flask + Flask-SQLAlchemy 3.1.1 + PostgreSQL**
- **HTMX** para partials (mismo patrón que `trabajadores.html`)
- **DataTables** para listados
- **Flask-Login** para `current_user`
- Todas las consultas usan `db.session.execute(select(...))` — nunca `Model.query`
- `db.session.remove()` en jobs de scheduler, no en requests normales

---

## CONTEXTO

El sistema SGT 2.1 ya genera cuadrantes de turno con el Solver (OR-Tools CP-SAT).
El cuadrante se visualiza en `planificacion.html` pero actualmente **no se persiste en BD**.

Necesito:
1. Guardar el cuadrante en BD al pulsar "Guardar Cuadrante" (renombrado desde "Publicar")
2. Permitir ediciones manuales post-guardado con auditoría por usuario logueado
3. Mostrar las últimas planificaciones en el dashboard como DataTable

El plan adjunto `plan_guardado_cuadrante.md` tiene el diseño completo de tablas,
modelos, servicios, endpoints y templates.

**REGLA**: Muéstrame el diff de cada paso y espera mi aprobación antes de continuar.

---

## PASO 1 — Crear tablas y modelos

Ejecuta el SQL de creación de las 3 tablas del plan:
- `cuadrante_cabecera`
- `cuadrante_asignacion`
- `cuadrante_auditoria`

Luego crea el archivo `app/models/scheduling.py` con los 3 modelos:
`CuadranteCabecera`, `CuadranteAsignacion`, `CuadranteAuditoria`.

Verifica que los nombres de tablas referenciadas en ForeignKey coincidan
exactamente con las tablas existentes en el proyecto (empresa, sucursal,
servicio, trabajador, turno, user).

Muéstrame el SQL y el modelo completo antes de continuar.

---

## PASO 2 — Crear `app/services/cuadrante_service.py`

Implementa las dos funciones del plan:
- `guardar_cuadrante(...)` → persiste cabecera + asignaciones con origen='solver'
  y los flags de clasificación de día (es_feriado, es_domingo, tipo_dia, etc.)
- `editar_asignacion_manual(...)` → modifica una asignación, registra en auditoría
  con current_user.id, turno anterior, turno nuevo e IP

Reglas:
- Todas las consultas usan `db.session.execute(select(...))`
- Si ya existe un cuadrante para ese período (sucursal + servicio + mes + año),
  eliminarlo antes de insertar el nuevo (reemplazar, no duplicar)
- La función `clasificar_dia` debe estar en este mismo archivo



---

## PASO 3 — Crear `app/controllers/cuadrante_bp.py`

Implementa el Blueprint `cuadrante_bp` con 3 endpoints:

1. `POST /cuadrante/guardar` → llama a `guardar_cuadrante()`
2. `PUT /cuadrante/asignacion/<int:asig_id>` → llama a `editar_asignacion_manual()`
3. `GET /cuadrante/lista` → retorna el partial de últimas planificaciones

Todos los endpoints requieren `@login_required`.



---

## PASO 4 — Registrar el blueprint en `app/__init__.py`

Agrega:
```python
from app.controllers.cuadrante_bp import cuadrante_bp
app.register_blueprint(cuadrante_bp)
```


---

## PASO 5 — Actualizar `planificacion.html`

Haz exactamente estos 3 cambios:

1. Renombrar el botón "Publicar" → "Guardar Cuadrante" (ícono `fa-save`, clase `btn-success`)
2. Agregar el JavaScript de guardado que hace `POST /cuadrante/guardar`
   con las variables `EMPRESA_ID`, `SUCURSAL_ID`, `SERVICIO_ID`, `MES`, `ANIO`
   que ya deben existir en el template como `window.X`
3. Agregar la función `activarModoEdicion()` que convierte el tooltip existente
   en un `<select>` de turnos al hacer clic en una celda post-guardado.
   Cada cambio hace `PUT /cuadrante/asignacion/{id}` y muestra `✏️` en la celda.



---

## PASO 6 — Crear `app/templates/cuadrante/lista_partial.html`

Crea el template siguiendo exactamente el mismo patrón de `trabajadores.html`:
- `extends "_partial.html" if is_htmx else "layout.html"`
- DataTable con columnas: Empresa/Sucursal | Servicio | Período | Estado |
  Asig. Manuales | Guardado por | Fecha | Acciones
- Badge `✏️ N` en columna "Asig. Manuales" si `c.total_manuales > 0`
- Botones de acción: Ver (`fa-eye`) y Editar (`fa-edit`)



---

## PASO 7 — Integrar en el dashboard

En `app/templates/dashboard.html`, en la sección "Últimas Planificaciones",
reemplaza el contenido estático actual por la carga HTMX del partial:

```html
<div hx-get="/cuadrante/lista"
     hx-trigger="load"
     hx-swap="innerHTML">
    <div class="text-center p-3">
        <div class="spinner-border spinner-border-sm"></div>
        Cargando planificaciones...
    </div>
</div>
```



---

## ARCHIVOS QUE NO DEBES TOCAR

- `app/scheduler/builder.py` — el motor de cuadrantes NO se modifica
- `app/services/legal_engine.py` — sin cambios
- `app/services/scheduling_service.py` — sin cambios
- Modelos existentes distintos de los nuevos

---

## VERIFICACIÓN FINAL

- [ ] 3 tablas creadas en BD con índices
- [ ] 3 modelos en `scheduling.py`
- [ ] `cuadrante_service.py` con `guardar_cuadrante` y `editar_asignacion_manual`
- [ ] Blueprint registrado en `__init__.py`
- [ ] Botón renombrado a "Guardar Cuadrante"
- [ ] Celdas editables post-guardado con `✏️` en cambios manuales
- [ ] DataTable "Últimas Planificaciones" en el dashboard

---

> Cualquier modificación fuera de los archivos indicados debe ser consultada
> y aprobada por el usuario antes de implementarse.

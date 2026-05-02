# PROMPT PARA ANTIGRAVITY — Implementación Feriados Automáticos SGT 2.1

> Adjunta este archivo junto con `plan_feriados_automaticos_v2.md` como contexto.
> Aplica los cambios en el orden indicado.
> NO implementes el siguiente paso sin mostrarme el diff y esperar mi aprobación.

---

## CONTEXTO

Estoy trabajando en SGT 2.1, un sistema de gestión de turnos en Flask + PostgreSQL.
Necesito implementar la sincronización automática de feriados chilenos usando la API
feriados.io y mostrarlos visualmente en el cuadrante de planificación.

El archivo adjunto `plan_feriados_automaticos_v2.md` contiene el diseño completo.
Implementa exactamente lo que describe, en el orden indicado.

**API key**: La API key ya está en el plan. Al escribir el código, declárala como
variable de entorno `FERIADOS_API_KEY` y agrégala al `.env`.

**REGLA**: Muéstrame el diff de cada paso y espera mi aprobación antes de continuar.

---

## PASO 1 — Ampliar el modelo `Feriado` en `app/models/core.py`

Agrega los siguientes campos al modelo existente `Feriado`:

```python
es_irrenunciable = db.Column(db.Boolean, default=False)
tipo             = db.Column(db.String(20), default='nacional')
fuente           = db.Column(db.String(50), default='feriados.io')
```

Agrega también las propiedades calculadas `es_domingo`, `tipo_display` y `badge_config`
exactamente como están definidas en el plan.

Luego genera el script de migración Flask-SQLAlchemy (o SQL directo si no usas Alembic):
```sql
ALTER TABLE feriado ADD COLUMN es_irrenunciable BOOLEAN DEFAULT FALSE;
ALTER TABLE feriado ADD COLUMN tipo VARCHAR(20) DEFAULT 'nacional';
ALTER TABLE feriado ADD COLUMN fuente VARCHAR(50) DEFAULT 'feriados.io';
CREATE INDEX idx_feriado_fecha ON feriado(fecha);
CREATE INDEX idx_feriado_activo ON feriado(activo, fecha);
```

Muéstrame el diff de `core.py` y el script SQL antes de continuar.

---

## PASO 2 — Crear `app/services/feriado_sync_service.py`

Crea el archivo nuevo con exactamente estas funciones:
- `es_irrenunciable(mes, dia, nombre)` — fallback para irrenunciables conocidos
- `sincronizar_feriados_anio(anio)` — sincroniza año completo desde la API
- `sincronizar_mes_siguiente()` — sincroniza solo el mes siguiente (para el scheduler)
- `carga_inicial(anios)` — pobla la tabla si está vacía

La lógica de actualización diferencial es crítica:
solo insertar o actualizar cuando hay diferencias reales.
No sobreescribir registros sin cambios.

Usa el endpoint de la API:
- Por año: `GET https://api.feriados.io/v1/CL/holidays/{anio}`
- Por mes: `GET https://api.feriados.io/v1/CL/holidays/{anio}/{mes}`
- Header: `Authorization: Bearer {FERIADOS_API_KEY}`

Muéstrame el archivo completo antes de continuar.

---

## PASO 3 — Crear `app/scheduler/feriado_scheduler.py`

Crea el archivo con APScheduler configurado para ejecutar
`sincronizar_mes_siguiente()` el día 1 de cada mes a las 02:00 AM
hora Chile (`America/Santiago`).

Función principal: `iniciar_scheduler_feriados(app)`
Función de cierre: `detener_scheduler_feriados()`

Dependencias requeridas (agregar a `requirements.txt`):
```
apscheduler>=3.10.0
requests>=2.31.0
```

Muéstrame el archivo completo antes de continuar.

---

## PASO 4 — Actualizar `app/__init__.py`

Dentro de `create_app()`, después de `db.create_all()`:

1. Si `Feriado.query.count() == 0` → ejecutar `carga_inicial()`
2. Si `FLASK_ENV != "testing"` → ejecutar `iniciar_scheduler_feriados(app)`

Muéstrame solo el diff del bloque que cambia dentro de `create_app()`.

---

## PASO 5 — Actualizar `app/templates/main/planificacion.html`

En los encabezados de columna del cuadrante (los `<th>` que representan cada día del mes):

1. Agregar la leyenda de colores sobre la tabla (badges explicativos).
2. En cada `<th>` de día, consultar si ese día es feriado y mostrar el badge
   correspondiente según `tipo_display`:
   - `irrenunciable-domingo` → badge rojo oscuro `F.Irr+Dom`
   - `irrenunciable`         → badge rojo `F.Irr`
   - `regional`              → badge morado `F.Reg`
   - `feriado-domingo`       → badge naranja `Fer+Dom`
   - `nacional`              → badge amarillo `Feriado`
   - domingo sin feriado     → badge azul `Dom`

Para que el template tenga acceso al diccionario de feriados, el controller
(`main_bp.py`) debe pasar `feriados_dict = {f.fecha: f for f in feriados_del_mes}`
al `render_template`.

Muéstrame el diff del template y del controller antes de continuar.

---

## PASO 6 — Agregar API key al `.env`

Agrega al archivo `.env` del proyecto:
```
FERIADOS_API_KEY=frd_79c25cdc001441e59cc3dd4dae2e125b
```



---

## VERIFICACIÓN FINAL

Después de todos los pasos, ejecuta mentalmente este checklist:

- [ ] `Feriado` tiene los 3 campos nuevos en el modelo y en la BD
- [ ] `feriado_sync_service.py` existe con las 4 funciones
- [ ] `feriado_scheduler.py` existe y el job está configurado para día 1 a las 02:00
- [ ] `create_app()` ejecuta carga inicial si la tabla está vacía
- [ ] El cuadrante muestra badges de color en días feriados y domingos
- [ ] La API key está en `.env` y no en el código fuente

---

## ARCHIVOS QUE NO DEBES TOCAR

- `app/scheduler/builder.py` — el motor de cuadrantes NO se modifica en esta tarea
- `app/services/legal_engine.py` — sin cambios
- Cualquier modelo que no sea `Feriado`

---

> Cualquier modificación fuera de los archivos indicados debe ser consultada
> y aprobada por el usuario antes de implementarse.

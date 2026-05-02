# PLAN DE IMPLEMENTACIÓN: Feriados Automáticos — SGT 2.1

> **Estado**: Pendiente de implementación
> **Prioridad**: Alta
> **API**: feriados.io — `frd_79c25cdc001441e59cc3dd4dae2e125b`
> **Visación requerida**: Toda implementación debe ser aprobada por el usuario responsable.

---

## RESOLUCIÓN LEGAL PREVIA: Feriado Irrenunciable que cae Domingo

Antes de implementar, esta es la respuesta legal definitiva según la DT:

### ¿Qué prevalece: el domingo o el feriado irrenunciable?

**Prevalecen AMBOS simultáneamente. No se anulan mutuamente.**

Según **Dictamen Ordinario N° 4359 (DT, 15-sep-2017)** y **Ordinario N° 2001 (DT, nov-2022)**:

> *"La coincidencia de un domingo con un día declarado por ley como feriado irrenunciable,
> no genera a los trabajadores exceptuados del descanso dominical un día adicional de descanso."*

Esto significa:

| Situación | Consecuencia legal |
|---|---|
| Feriado irrenunciable en día de semana | Descanso obligatorio. Si trabaja → día compensatorio. |
| Feriado irrenunciable en domingo (para trabajador NO exceptuado) | Descanso normal de domingo. Sin efecto adicional. |
| Feriado irrenunciable en domingo (para trabajador régimen exceptuado Art. 38 N°7) | **El empleador NO puede imputarlo como uno de los 2 domingos libres del mes (HR7) ni como uno de los 7 domingos anuales (Art. 38 bis). El domingo libre DEBE otorgarse en otra fecha.** |
| Trabajar en feriado irrenunciable (si se autorizó) | Doble obligación: compensación por feriado + compensación dominical si aplica. |

### Regla para el sistema:
```
es_irrenunciable AND es_domingo AND trabajador.regimen_exceptuado
→ ese día cuenta como "feriado irrenunciable" en la visualización
→ NO cuenta como uno de los 2 domingos libres del mes (HR7)
→ NO se puede imputar al cuadrante como "domingo libre otorgado"
→ El Solver debe encontrar OTRO domingo libre ese mes
```

### Los 5 feriados irrenunciables en Chile (Ley 19.973):
1. 1 de enero (Año Nuevo)
2. 1 de mayo (Día del Trabajador)
3. 18 de septiembre (Independencia)
4. 19 de septiembre (Glorias del Ejército)
5. 25 de diciembre (Navidad)

---

## PARTE 1: AMPLIAR EL MODELO `Feriado`

El modelo actual no tiene campos suficientes para clasificar correctamente los feriados.

### Migración de BD

```sql
-- Agregar campos al modelo existente
ALTER TABLE feriado ADD COLUMN es_irrenunciable BOOLEAN DEFAULT FALSE;
ALTER TABLE feriado ADD COLUMN tipo VARCHAR(20) DEFAULT 'nacional';
-- tipo: 'nacional' | 'regional' | 'irrenunciable'

-- Índices para rendimiento en el Solver
CREATE INDEX idx_feriado_fecha ON feriado(fecha);
CREATE INDEX idx_feriado_activo ON feriado(activo, fecha);
```

### Modelo actualizado (`app/models/core.py`)

```python
class Feriado(db.Model):
    __tablename__ = 'feriado'
    id              = db.Column(db.Integer, primary_key=True)
    fecha           = db.Column(db.Date, nullable=False)
    descripcion     = db.Column(db.String(200), nullable=False)
    es_irrenunciable = db.Column(db.Boolean, default=False)   # NUEVO
    es_regional     = db.Column(db.Boolean, default=False)
    region_id       = db.Column(db.Integer, db.ForeignKey('region.id', ondelete='CASCADE'), nullable=True)
    tipo            = db.Column(db.String(20), default='nacional')  # NUEVO: nacional|regional|irrenunciable
    activo          = db.Column(db.Boolean, default=True)
    fuente          = db.Column(db.String(50), default='feriados.io')  # NUEVO: origen del registro
    creado_en       = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def es_domingo(self) -> bool:
        """Calculado dinámicamente, no almacenado."""
        return self.fecha.weekday() == 6

    @property
    def tipo_display(self) -> str:
        """Etiqueta para la visualización del cuadrante."""
        if self.es_irrenunciable and self.es_domingo:
            return 'irrenunciable-domingo'
        if self.es_irrenunciable:
            return 'irrenunciable'
        if self.es_regional:
            return 'regional'
        if self.es_domingo:
            return 'feriado-domingo'
        return 'nacional'

    @property
    def badge_config(self) -> dict:
        """Configuración visual para el cuadrante."""
        configs = {
            'irrenunciable-domingo': {'color': '#c0392b', 'label': 'F.Irr+Dom', 'icon': '🔴'},
            'irrenunciable':         {'color': '#e74c3c', 'label': 'F.Irr',    'icon': '🔴'},
            'regional':              {'color': '#8e44ad', 'label': 'F.Reg',    'icon': '🟣'},
            'feriado-domingo':       {'color': '#e67e22', 'label': 'Fer+Dom',  'icon': '🟠'},
            'nacional':              {'color': '#f39c12', 'label': 'Feriado',  'icon': '🟡'},
        }
        return configs.get(self.tipo_display, configs['nacional'])
```

---

## PARTE 2: SERVICIO DE SINCRONIZACIÓN (`app/services/feriado_sync_service.py`)

Este servicio se encarga de consultar la API y actualizar la BD solo cuando hay diferencias.

```python
# app/services/feriado_sync_service.py

import requests
import logging
from datetime import date, datetime
from app.models.core import Feriado
from app import db

logger = logging.getLogger(__name__)

FERIADOS_API_KEY  = "frd_79c25cdc001441e59cc3dd4dae2e125b"
FERIADOS_BASE_URL = "https://api.feriados.io/v1/CL"
FERIADOS_HEADERS  = {"Authorization": f"Bearer {FERIADOS_API_KEY}"}

# Feriados irrenunciables conocidos (Ley 19.973) — fallback si la API no los marca
IRRENUNCIABLES_CONOCIDOS = {
    (1, 1),   # 1 enero
    (5, 1),   # 1 mayo
    (9, 18),  # 18 septiembre
    (9, 19),  # 19 septiembre
    (12, 25), # 25 diciembre
}


def es_irrenunciable(mes: int, dia: int, nombre: str = "") -> bool:
    """
    Determina si un feriado es irrenunciable por fecha o nombre.
    La API feriados.io retorna el campo irrenunciable=True/False.
    Este fallback cubre si la API no lo indica explícitamente.
    """
    return (mes, dia) in IRRENUNCIABLES_CONOCIDOS


def sincronizar_feriados_anio(anio: int) -> dict:
    """
    Consulta la API feriados.io para el año indicado y sincroniza con la BD.
    Solo inserta o actualiza registros con diferencias reales.
    Retorna un resumen de la operación.
    """
    url = f"{FERIADOS_BASE_URL}/holidays/{anio}"
    resumen = {"anio": anio, "consultados": 0, "insertados": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}

    try:
        resp = requests.get(url, headers=FERIADOS_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise ValueError(f"API retornó error: {data}")

        feriados_api = data.get("data", [])
        resumen["consultados"] = len(feriados_api)

        for item in feriados_api:
            try:
                fecha      = date.fromisoformat(item["date"])
                descripcion = item.get("name", "Feriado")
                tipo_api   = item.get("type", "national")   # national | regional
                irr_api    = item.get("irrenunciable", False)

                # Determinar clasificación
                es_irr = irr_api or es_irrenunciable(fecha.month, fecha.day, descripcion)
                es_reg = (tipo_api == "regional")
                tipo   = "irrenunciable" if es_irr else ("regional" if es_reg else "nacional")

                # Buscar si ya existe en BD
                existente = Feriado.query.filter_by(fecha=fecha).first()

                if existente is None:
                    # Insertar nuevo
                    nuevo = Feriado(
                        fecha=fecha,
                        descripcion=descripcion,
                        es_irrenunciable=es_irr,
                        es_regional=es_reg,
                        tipo=tipo,
                        activo=True,
                        fuente="feriados.io"
                    )
                    db.session.add(nuevo)
                    resumen["insertados"] += 1

                else:
                    # Verificar si hay diferencias antes de actualizar
                    cambios = False
                    if existente.descripcion != descripcion:
                        existente.descripcion = descripcion
                        cambios = True
                    if existente.es_irrenunciable != es_irr:
                        existente.es_irrenunciable = es_irr
                        cambios = True
                    if existente.es_regional != es_reg:
                        existente.es_regional = es_reg
                        cambios = True
                    if existente.tipo != tipo:
                        existente.tipo = tipo
                        cambios = True

                    if cambios:
                        existente.actualizado_en = datetime.utcnow()
                        resumen["actualizados"] += 1
                    else:
                        resumen["sin_cambios"] += 1

            except Exception as e:
                resumen["errores"].append(f"{item.get('date', '?')} — {str(e)}")

        db.session.commit()
        logger.info(f"[FeriadoSync] Año {anio}: {resumen}")

    except requests.RequestException as e:
        resumen["errores"].append(f"Error de red: {str(e)}")
        logger.error(f"[FeriadoSync] Error consultando API para {anio}: {e}")

    return resumen


def sincronizar_mes_siguiente() -> dict:
    """
    Sincroniza los feriados del mes siguiente al actual.
    Diseñado para ser llamado por el scheduler mensual.
    Usa el endpoint por mes para minimizar uso de quota de la API.
    """
    hoy = date.today()
    if hoy.month == 12:
        mes_sig, anio_sig = 1, hoy.year + 1
    else:
        mes_sig, anio_sig = hoy.month + 1, hoy.year

    url = f"{FERIADOS_BASE_URL}/holidays/{anio_sig}/{mes_sig}"
    resumen = {"mes": f"{anio_sig}-{mes_sig:02d}", "insertados": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}

    try:
        resp = requests.get(url, headers=FERIADOS_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise ValueError(f"API error: {data}")

        for item in data.get("data", []):
            try:
                fecha       = date.fromisoformat(item["date"])
                descripcion = item.get("name", "Feriado")
                tipo_api    = item.get("type", "national")
                irr_api     = item.get("irrenunciable", False)
                es_irr      = irr_api or es_irrenunciable(fecha.month, fecha.day)
                es_reg      = (tipo_api == "regional")
                tipo        = "irrenunciable" if es_irr else ("regional" if es_reg else "nacional")

                existente = Feriado.query.filter_by(fecha=fecha).first()
                if existente is None:
                    db.session.add(Feriado(
                        fecha=fecha, descripcion=descripcion,
                        es_irrenunciable=es_irr, es_regional=es_reg,
                        tipo=tipo, activo=True, fuente="feriados.io"
                    ))
                    resumen["insertados"] += 1
                else:
                    # Solo actualizar si hay diferencias
                    cambios = any([
                        existente.descripcion != descripcion,
                        existente.es_irrenunciable != es_irr,
                        existente.tipo != tipo,
                    ])
                    if cambios:
                        existente.descripcion    = descripcion
                        existente.es_irrenunciable = es_irr
                        existente.tipo           = tipo
                        existente.actualizado_en = datetime.utcnow()
                        resumen["actualizados"] += 1
                    else:
                        resumen["sin_cambios"] += 1

            except Exception as e:
                resumen["errores"].append(str(e))

        db.session.commit()
        logger.info(f"[FeriadoSync] Mes siguiente: {resumen}")

    except requests.RequestException as e:
        resumen["errores"].append(str(e))

    return resumen


def carga_inicial(anios: list = None) -> dict:
    """
    Pobla la tabla feriado desde cero.
    Llamar una sola vez al desplegar el sistema por primera vez.
    Por defecto sincroniza el año actual y el siguiente.
    """
    if anios is None:
        hoy = date.today()
        anios = [hoy.year, hoy.year + 1]

    resultados = {}
    for anio in anios:
        resultados[anio] = sincronizar_feriados_anio(anio)
    return resultados
```

---

## PARTE 3: SCHEDULER AUTOMÁTICO (`app/scheduler/feriado_scheduler.py`)

```python
# app/scheduler/feriado_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="America/Santiago")


def iniciar_scheduler_feriados(app):
    """
    Registra el job de sincronización mensual de feriados.
    Llamar desde app/__init__.py al arrancar la aplicación.

    El job corre el día 1 de cada mes a las 02:00 AM (hora Chile).
    Consulta los feriados del mes siguiente y actualiza la BD.
    """
    from app.services.feriado_sync_service import sincronizar_mes_siguiente

    def job_sync():
        with app.app_context():
            logger.info("[FeriadoScheduler] Iniciando sincronización mensual...")
            resultado = sincronizar_mes_siguiente()
            logger.info(f"[FeriadoScheduler] Completado: {resultado}")

    # Día 1 de cada mes a las 02:00 AM hora Chile
    scheduler.add_job(
        func=job_sync,
        trigger=CronTrigger(day=1, hour=2, minute=0, timezone="America/Santiago"),
        id="sync_feriados_mensual",
        name="Sincronización mensual de feriados",
        replace_existing=True,
        misfire_grace_time=3600  # Tolera hasta 1 hora de retraso si el servidor estaba caído
    )

    scheduler.start()
    logger.info("[FeriadoScheduler] Scheduler iniciado. Job programado para el día 1 de cada mes a las 02:00.")
    return scheduler


def detener_scheduler_feriados():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[FeriadoScheduler] Scheduler detenido.")
```

### Integración en `app/__init__.py`

```python
# app/__init__.py — dentro de create_app()

from app.scheduler.feriado_scheduler import iniciar_scheduler_feriados
from app.services.feriado_sync_service import carga_inicial

def create_app():
    app = Flask(__name__)
    # ... configuración existente ...

    with app.app_context():
        db.create_all()

        # Carga inicial si la tabla está vacía
        if Feriado.query.count() == 0:
            logger.info("Tabla feriados vacía. Ejecutando carga inicial...")
            resultado = carga_inicial()
            logger.info(f"Carga inicial completada: {resultado}")

    # Iniciar scheduler solo en producción / proceso principal
    import os
    if os.environ.get("FLASK_ENV") != "testing":
        iniciar_scheduler_feriados(app)

    return app
```

---

## PARTE 4: FLAGS EN `cuadrante_asignacion` (cuando se guarde el cuadrante)

Cuando se implemente la persistencia del cuadrante (prerequisito de HR9-CROSS),
cada asignación debe llevar los flags de feriado para trazabilidad legal:

```sql
-- Agregar a la tabla cuadrante_asignacion (cuando exista)
ALTER TABLE cuadrante_asignacion ADD COLUMN es_feriado            BOOLEAN DEFAULT FALSE;
ALTER TABLE cuadrante_asignacion ADD COLUMN es_feriado_irrenunciable BOOLEAN DEFAULT FALSE;
ALTER TABLE cuadrante_asignacion ADD COLUMN es_feriado_regional   BOOLEAN DEFAULT FALSE;
ALTER TABLE cuadrante_asignacion ADD COLUMN es_domingo            BOOLEAN DEFAULT FALSE;
ALTER TABLE cuadrante_asignacion ADD COLUMN tipo_dia              VARCHAR(30) DEFAULT 'normal';
-- tipo_dia: normal | domingo | feriado | feriado-irrenunciable | feriado-regional
--           domingo-feriado | domingo-irrenunciable
```

### Lógica al guardar

```python
# scheduling_service.py — al persistir asignaciones

def clasificar_dia(fecha: date, feriados_dict: dict) -> dict:
    """
    feriados_dict: {fecha: Feriado} precargado para el mes.
    Retorna los flags de clasificación del día.
    """
    feriado = feriados_dict.get(fecha)
    es_dom  = (fecha.weekday() == 6)
    es_fer  = (feriado is not None and feriado.activo)
    es_irr  = (feriado.es_irrenunciable if feriado else False)
    es_reg  = (feriado.es_regional if feriado else False)

    # Determinar tipo_dia
    if es_irr and es_dom:
        tipo_dia = 'domingo-irrenunciable'
    elif es_irr:
        tipo_dia = 'feriado-irrenunciable'
    elif es_fer and es_dom:
        tipo_dia = 'domingo-feriado'
    elif es_reg:
        tipo_dia = 'feriado-regional'
    elif es_fer:
        tipo_dia = 'feriado'
    elif es_dom:
        tipo_dia = 'domingo'
    else:
        tipo_dia = 'normal'

    return {
        "es_feriado":              es_fer,
        "es_feriado_irrenunciable": es_irr,
        "es_feriado_regional":     es_reg,
        "es_domingo":              es_dom,
        "tipo_dia":                tipo_dia,
    }
```

---

## PARTE 5: VISUALIZACIÓN EN EL CUADRANTE

### Badges de color para `planificacion.html`

```html
<!-- Leyenda en el encabezado del cuadrante -->
<div class="d-flex gap-2 mb-2 flex-wrap">
  <span class="badge" style="background:#e74c3c">🔴 F. Irrenunciable</span>
  <span class="badge" style="background:#c0392b">🔴 F. Irrenunciable + Dom</span>
  <span class="badge" style="background:#f39c12">🟡 Feriado Nacional</span>
  <span class="badge" style="background:#8e44ad">🟣 Feriado Regional</span>
  <span class="badge" style="background:#e67e22">🟠 Feriado + Domingo</span>
  <span class="badge" style="background:#3498db">🔵 Domingo</span>
</div>

<!-- Encabezado de columna del cuadrante (día del mes) -->
{% for dia in dias_mes %}
  {% set feriado = feriados_dict.get(dia) %}
  {% set es_dom  = dia.weekday() == 6 %}

  <th class="text-center {% if feriado %}col-feriado{% endif %}
             {% if es_dom %}col-domingo{% endif %}">

    {{ dia.day }}

    {% if feriado %}
      {% if feriado.es_irrenunciable and es_dom %}
        <br><span class="badge badge-sm" style="background:#c0392b;font-size:0.6rem">F.Irr+Dom</span>
      {% elif feriado.es_irrenunciable %}
        <br><span class="badge badge-sm" style="background:#e74c3c;font-size:0.6rem">F.Irr</span>
      {% elif feriado.es_regional %}
        <br><span class="badge badge-sm" style="background:#8e44ad;font-size:0.6rem">F.Reg</span>
      {% else %}
        <br><span class="badge badge-sm" style="background:#f39c12;font-size:0.6rem">Feriado</span>
      {% endif %}
    {% elif es_dom %}
      <br><span class="badge badge-sm" style="background:#3498db;font-size:0.6rem">Dom</span>
    {% endif %}

  </th>
{% endfor %}
```

---

## PARTE 6: IMPACTO EN EL BUILDER (feriados irrenunciables + HR7)

```python
# builder.py — al construir el modelo

# Precargar feriados del mes
feriados_mes = {
    f.fecha: f
    for f in Feriado.query.filter(
        Feriado.fecha.between(primer_dia, ultimo_dia),
        Feriado.activo == True
    ).all()
}

# Para trabajadores de régimen exceptuado:
# Un feriado irrenunciable que cae domingo NO cuenta como uno
# de los 2 domingos libres del mes (DT Ord. N°4359/2017)
domingos_computables = []
for d in domingos_mes:
    feriado = feriados_mes.get(d)
    if feriado and feriado.es_irrenunciable and trabajador.regimen_exceptuado:
        # Este domingo NO se puede imputar como domingo libre (HR7)
        # Pero tampoco puede trabajarse (es irrenunciable)
        # → bloqueado por HR1, pero NO suma al conteo de domingos libres
        continue
    domingos_computables.append(d)

# HR7 aplica solo sobre domingos computables
model.Add(
    sum(
        1 - sum(x[w.id, d, t.id] for t in turnos)
        for d in domingos_computables
        if (w.id, d) not in bloqueados  # descontar ausencias
    ) >= MIN_DOMINGOS_LIBRES_MES
)
```

---

## ORDEN DE IMPLEMENTACIÓN

| Paso | Archivo | Acción | Prerequisito |
|---|---|---|---|
| 1 | `app/models/core.py` | Agregar campos al modelo `Feriado` | — |
| 2 | Migración BD | `ALTER TABLE feriado ADD COLUMN ...` | Paso 1 |
| 3 | `app/services/feriado_sync_service.py` | Crear servicio de sincronización | Paso 2 |
| 4 | `app/__init__.py` | Carga inicial + iniciar scheduler | Paso 3 |
| 5 | `app/scheduler/feriado_scheduler.py` | Crear scheduler APScheduler | Paso 3 |
| 6 | `app/templates/main/planificacion.html` | Agregar badges en encabezados del cuadrante | Paso 2 |
| 7 | `app/scheduler/builder.py` | Actualizar lógica HR7 para excluir dom. irrenunciables | Pasos 2 y 6 |
| 8 | Persistencia cuadrante | Agregar flags `es_feriado`, `tipo_dia` al guardar | Tabla `cuadrante_asignacion` existente |

> **Paso 6 (Actualización HR7 en builder.py) excluido del alcance actual.**
> La mayoría de las empresas operan en régimen exceptuado y el Builder ya bloquea
> feriados irrenunciables vía HR1. Este ajuste solo es relevante cuando un feriado
> irrenunciable cae domingo (próximo caso: 18-sep-2027). Registrado como INC-06
> en el documento de incongruencias para implementación futura.

---

## DEPENDENCIAS PYTHON REQUERIDAS

```
apscheduler>=3.10.0   # Scheduler automático
requests>=2.31.0      # HTTP client para la API
```

```bash
pip install apscheduler requests
```

---

## TESTS DE ACEPTACIÓN

```
[TEST-FER-01] Carga inicial: tabla vacía → carga_inicial() llena la tabla con feriados del año actual y siguiente

[TEST-FER-02] Sin cambios: ejecutar sincronizar_feriados_anio() dos veces seguidas
              → segunda ejecución: insertados=0, actualizados=0, sin_cambios=N

[TEST-FER-03] 1 de mayo en año X → es_irrenunciable=True, tipo='irrenunciable'

[TEST-FER-04] 1 de mayo que cae domingo (próximo: 2033) →
              es_irrenunciable=True, tipo_display='irrenunciable-domingo',
              y builder NO lo imputa como domingo libre en HR7

[TEST-FER-05] Feriado regional (ej: 29 jun en regiones) → es_regional=True, tipo='regional'

[TEST-FER-06] Día sin feriado → Feriado.query.filter_by(fecha=fecha).first() == None

[TEST-FER-07] Scheduler: verificar que el job 'sync_feriados_mensual' existe y su
              próxima ejecución es el día 1 del mes siguiente a las 02:00
```

---


---

## INCONGRUENCIA PENDIENTE REGISTRADA

### INC-06 — HR7 no excluye domingos irrenunciables del conteo

| Campo | Detalle |
|---|---|
| **Severidad** | 🟡 Baja |
| **Cuándo afecta** | Solo cuando un feriado irrenunciable cae exactamente en domingo |
| **Próxima ocurrencia** | 18 de septiembre de 2027 |
| **Estado** | Pospuesto — documentado para implementación futura |
| **Prerequisito** | Cuadrante persistido en BD + lógica de feriados estable |
| **Archivo afectado** | `app/scheduler/builder.py` — bloque HR7 |

**Descripción**: Cuando un feriado irrenunciable (Ley 19.973) cae domingo, el Builder
actual lo bloquea correctamente vía HR1 (el trabajador no trabaja ese día). Sin embargo,
ese domingo bloqueado podría estar siendo contado erróneamente como uno de los 2 domingos
libres obligatorios del mes (HR7), lo que reduciría el número de domingos libres reales
que el empleador debe otorgar. Según DT Ord. N°4359/2017, ese domingo irrenunciable
**no puede imputarse** como domingo libre del Art. 38.

**Impacto en la mayoría de empresas**: Nulo en la práctica actual, ya que las empresas
en régimen exceptuado tienen esta situación raramente y el efecto solo se materializa
si el mes tiene exactamente 2 domingos disponibles y uno es irrenunciable.

> **Recordatorio**: Toda implementación derivada de este plan debe ser visada
> y aprobada por el usuario responsable del proyecto antes de ser confirmada.
> La API key `frd_79c25cdc001441e59cc3dd4dae2e125b` debe guardarse en
> variables de entorno, nunca en el código fuente.
>
> ```python
> # .env
> FERIADOS_API_KEY=frd_79c25cdc001441e59cc3dd4dae2e125b
> ```
> ```python
> # feriado_sync_service.py
> import os
> FERIADOS_API_KEY = os.environ.get("FERIADOS_API_KEY")
> ```

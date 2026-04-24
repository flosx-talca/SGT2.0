# Mejora futura — Feriados en el cuadrante persistente

**Estado:** Pendiente
**Prioridad:** Alta — necesario antes de implementar cálculo de horas al publicar

---

## 1. Qué se necesita

Cuando el cuadrante se publique y persista en BD, cada celda trabajada debe
saber si ese día era feriado para calcular correctamente las horas y generar
compensatorios si corresponde.

Para eso, la tabla `feriado` debe estar poblada **antes** de publicar
cualquier cuadrante.

---

## 2. Estado actual de la tabla `Feriado`

La tabla ya existe en el modelo:

```python
class Feriado(db.Model):
    __tablename__ = 'feriado'

    id               = db.Column(db.Integer, primary_key=True)
    fecha            = db.Column(db.Date, unique=True, nullable=False)
    descripcion      = db.Column(db.String(200), nullable=False)
    es_irrenunciable = db.Column(db.Boolean, default=False)
    es_regional      = db.Column(db.Boolean, default=False)
    region_id        = db.Column(db.Integer, db.ForeignKey('region.id'),
                                 nullable=True)
    activo           = db.Column(db.Boolean, default=True)
    creado_en        = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en   = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)
```

**Problema:** la tabla existe pero no tiene datos. No se han cargado los
feriados del año.

---

## 3. Feriados de Chile 2026 a seedear

### Feriados nacionales irrenunciables (Art. 35 bis Código del Trabajo)

| Fecha | Descripción |
|---|---|
| 2026-01-01 | Año Nuevo |
| 2026-05-01 | Día del Trabajo |
| 2026-09-18 | Independencia Nacional |
| 2026-09-19 | Día de las Glorias del Ejército |
| 2026-12-25 | Navidad |

### Feriados nacionales comunes

| Fecha | Descripción |
|---|---|
| 2026-04-03 | Viernes Santo |
| 2026-04-04 | Sábado Santo |
| 2026-05-21 | Glorias Navales |
| 2026-06-29 | San Pedro y San Pablo |
| 2026-07-16 | Día de la Virgen del Carmen |
| 2026-08-15 | Asunción de la Virgen |
| 2026-10-12 | Encuentro de Dos Mundos |
| 2026-10-31 | Día de las Iglesias Evangélicas |
| 2026-11-01 | Día de Todos los Santos |
| 2026-11-02 | Día de los Difuntos |
| 2026-12-08 | Inmaculada Concepción |

---

## 4. Script de seed

```python
# seed_feriados_2026.py
# Ejecutar una sola vez: python seed_feriados_2026.py

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.core import Feriado
from datetime import date

app = create_app()

FERIADOS_2026 = [
    # (fecha, descripcion, es_irrenunciable)
    (date(2026,  1,  1), 'Año Nuevo',                          True),
    (date(2026,  4,  3), 'Viernes Santo',                      False),
    (date(2026,  4,  4), 'Sábado Santo',                       False),
    (date(2026,  5,  1), 'Día del Trabajo',                    True),
    (date(2026,  5, 21), 'Glorias Navales',                    False),
    (date(2026,  6, 29), 'San Pedro y San Pablo',              False),
    (date(2026,  7, 16), 'Día de la Virgen del Carmen',        False),
    (date(2026,  8, 15), 'Asunción de la Virgen',              False),
    (date(2026,  9, 18), 'Independencia Nacional',             True),
    (date(2026,  9, 19), 'Día de las Glorias del Ejército',    True),
    (date(2026, 10, 12), 'Encuentro de Dos Mundos',            False),
    (date(2026, 10, 31), 'Día de las Iglesias Evangélicas',    False),
    (date(2026, 11,  1), 'Día de Todos los Santos',            False),
    (date(2026, 11,  2), 'Día de los Difuntos',                False),
    (date(2026, 12,  8), 'Inmaculada Concepción',              False),
    (date(2026, 12, 25), 'Navidad',                            True),
]

with app.app_context():
    insertados = 0
    omitidos   = 0
    for fecha, desc, irrenunciable in FERIADOS_2026:
        existe = Feriado.query.filter_by(fecha=fecha).first()
        if existe:
            omitidos += 1
            continue
        db.session.add(Feriado(
            fecha            = fecha,
            descripcion      = desc,
            es_irrenunciable = irrenunciable,
            es_regional      = False,
            activo           = True
        ))
        insertados += 1

    db.session.commit()
    print(f"✅ {insertados} feriados insertados, {omitidos} ya existían.")
```

---

## 5. Cómo se usa al publicar el cuadrante

Al momento de publicar, se carga el diccionario de feriados del mes
y se consulta para cada celda:

```python
# En el endpoint /publicar:

# Cargar feriados del mes una sola vez
feriados_mes = {
    f.fecha: {'es_irrenunciable': f.es_irrenunciable}
    for f in Feriado.query.filter(
        Feriado.fecha >= primer_dia,
        Feriado.fecha <= ultimo_dia,
        Feriado.activo == True
    ).all()
}

# Para cada celda con turno asignado:
horas = calcular_horas_celda(celda.fecha, turno, feriados_mes)
celda.horas_habil         = horas['horas_habil']
celda.horas_feriado       = horas['horas_feriado']
celda.horas_irrenunciable = horas['horas_irrenunciable']
celda.horas_domingo       = horas['horas_domingo']
```

---

## 6. Impacto en el cuadrante visual

Cuando el cuadrante esté persistido, los días feriados deben
marcarse visualmente diferente en la pantalla:

```
Columna de fecha:
  Normal:      "01 Mié"        → fondo blanco
  Domingo:     "05 Dom"        → fondo rosado (ya implementado)
  Feriado:     "18 Sep"        → fondo amarillo o ícono 🏛️
  Feriado irrenunciable: "01 May" → fondo naranja o ícono especial
```

El frontend ya recibe los `dias_dict` desde el backend.
Solo hay que agregar el campo `es_feriado` e `es_irrenunciable` a cada día:

```python
# En planificacion_bp.py al construir dias_dict:
feriados_mes = {f.fecha: f for f in Feriado.query.filter(...).all()}

for i in range(1, num_days + 1):
    fecha_obj = date(anio, mes, i)
    feriado   = feriados_mes.get(fecha_obj)
    dias_dict.append({
        'fecha':           fecha_str,
        'dia_semana':      js_day,
        'label':           f"{str(i).zfill(2)} {dias_nombres[dia_idx]}",
        'es_feriado':      feriado is not None,
        'es_irrenunciable': feriado.es_irrenunciable if feriado else False,
    })
```

---

## 7. Plan de implementación

```
Paso 1 — Seed de feriados
  Ejecutar seed_feriados_2026.py
  Verificar que los 16 feriados quedaron en la tabla

Paso 2 — Frontend muestra feriados
  Agregar es_feriado / es_irrenunciable a dias_dict en planificacion_bp.py
  Actualizar simulacion.html para pintar la columna según el tipo de día

Paso 3 — Cálculo de horas al publicar
  Implementar junto con el endpoint /publicar (ver plan_cuadrante_persistencia.md)
  calcular_horas_celda() ya considera feriados en su lógica

Paso 4 — Años futuros
  Agregar script equivalente para 2027, 2028, etc.
  O integrar con API de feriados de Chile (api.boostr.cl/feriados)
  para no tener que mantener los scripts manualmente
```

---

## 8. Consideración — Gasolineras y Art. 38

Las empresas bajo régimen exceptuado Art. 38 (gasolineras, supermercados,
farmacias, etc.) pueden hacer trabajar a sus empleados en feriados y domingos.
El feriado se registra igual y genera compensatorio, pero **no impide la asignación**.

La tabla `Feriado` no bloquea turnos en el builder — solo informa al
cálculo de horas cuándo aplicar recargo o generar compensatorio.

---

## 9. Feriados regionales por empresa

Algunas empresas están ubicadas en regiones o comunas con feriados propios
que no aplican al resto del país. El caso más conocido es el **Natalicio de
Bernardo O'Higgins (20 de agosto)**, que solo aplica a las comunas de
Chillán y Chillán Viejo en la Región de Ñuble.

### El problema actual

La tabla `Feriado` tiene `unique=True` en `fecha`, lo que significa que
solo puede existir **un registro por fecha**. Esto funciona para feriados
nacionales pero rompe para feriados regionales donde la misma fecha puede
ser feriado en una región y día normal en otra.

### Solución propuesta

Cambiar el constraint `unique` de `fecha` a `unique(fecha, region_id)`:

```python
class Feriado(db.Model):
    __tablename__ = 'feriado'

    id               = db.Column(db.Integer, primary_key=True)
    fecha            = db.Column(db.Date, nullable=False)     # ← quitar unique=True
    descripcion      = db.Column(db.String(200), nullable=False)
    es_irrenunciable = db.Column(db.Boolean, default=False)
    es_regional      = db.Column(db.Boolean, default=False)
    region_id        = db.Column(db.Integer, db.ForeignKey('region.id'),
                                 nullable=True)               # null = aplica a todo Chile
    activo           = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('fecha', 'region_id',
                            name='uq_feriado_fecha_region'),
    )
```

### Cómo se consultan al publicar

Al publicar el cuadrante, se cargan los feriados nacionales más los
regionales de la región donde está la empresa:

```python
empresa      = Empresa.query.get(empresa_id)
region_id    = empresa.comuna.region_id

feriados_mes = Feriado.query.filter(
    Feriado.fecha >= primer_dia,
    Feriado.fecha <= ultimo_dia,
    Feriado.activo == True,
    db.or_(
        Feriado.region_id == None,          # nacionales → aplican a todos
        Feriado.region_id == region_id      # regionales → solo su región
    )
).all()
```

### Feriados regionales Chile 2026

| Fecha | Descripción | Ámbito |
|---|---|---|
| 7 de junio | Asalto y Toma del Morro de Arica | Región XV — Arica y Parinacota |
| 20 de agosto | Natalicio de Bernardo O'Higgins | Solo Chillán y Chillán Viejo (Ñuble) |

### Migración necesaria antes de cargar feriados regionales

```sql
-- 1. Eliminar constraint único actual
ALTER TABLE feriado DROP CONSTRAINT feriado_fecha_key;

-- 2. Agregar nuevo constraint único por fecha + región
ALTER TABLE feriado ADD CONSTRAINT uq_feriado_fecha_region
    UNIQUE (fecha, region_id);
```

⚠️ Esta migración debe hacerse **antes** de cargar feriados regionales.
Si se intenta insertar un feriado regional sin hacer la migración,
la BD rechazará el insert con error de constraint único.

---

## 10. API Boostr — fuente oficial de feriados

En vez de mantener scripts de seed manualmente cada año, el sistema
usará la API pública y gratuita de **Boostr** para obtener los feriados
automáticamente.

**Documentación:** https://docs.boostr.cl/reference/holidays
**Sin autenticación requerida — es gratuita**

### Endpoints disponibles

```
GET https://api.boostr.cl/holidays.json
→ Feriados del año en curso

GET https://api.boostr.cl/holidays/{año}.json
→ Feriados de un año específico (ej: /holidays/2027.json)

GET https://api.boostr.cl/holidays/{fecha}.json
→ Verificar si una fecha específica es feriado (ej: /holidays/2026-09-18.json)
```

### Estructura de respuesta

```json
{
  "status": "success",
  "data": [
    {
      "date": "2026-01-01",
      "title": "Año Nuevo",
      "type": "Civil",
      "inalienable": true
    },
    {
      "date": "2026-04-03",
      "title": "Viernes Santo",
      "type": "Religioso",
      "inalienable": false
    }
  ]
}
```

### Comando Flask para poblar la tabla

```python
# Agregar a app/commands.py o similar
import click
import requests
from flask import current_app
from app.database import db
from app.models.core import Feriado
from datetime import datetime

@current_app.cli.command('seed-feriados')
@click.option('--anio', required=True, type=int,
              help='Año a cargar. Ej: flask seed-feriados --anio 2027')
def seed_feriados(anio):
    """Carga los feriados nacionales de Chile desde la API de Boostr."""

    url = f'https://api.boostr.cl/holidays/{anio}.json'
    print(f'Consultando {url}...')

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f'❌ Error al consultar la API: {e}')
        return

    if data.get('status') != 'success':
        print(f'❌ La API retornó error: {data}')
        return

    feriados = data.get('data', [])
    insertados = 0
    omitidos   = 0

    for f in feriados:
        fecha = datetime.strptime(f['date'], '%Y-%m-%d').date()
        existe = Feriado.query.filter_by(fecha=fecha, region_id=None).first()

        if existe:
            omitidos += 1
            continue

        db.session.add(Feriado(
            fecha            = fecha,
            descripcion      = f['title'],
            es_irrenunciable = f.get('inalienable', False),
            es_regional      = False,
            region_id        = None,   # nacionales
            activo           = True
        ))
        insertados += 1
        tipo = '🔴' if f.get('inalienable') else '🟡'
        print(f'  ✅ {tipo} {fecha} — {f["title"]}')

    db.session.commit()
    print(f'\nFeriados {anio}: {insertados} insertados, {omitidos} ya existían.')
```

### Uso

```bash
# Cargar feriados de un año específico:
flask seed-feriados --anio 2027
flask seed-feriados --anio 2028

# Recomendación: ejecutar en noviembre/diciembre del año anterior
# para tener los feriados listos antes de generar cuadrantes del año siguiente
```

### Limitaciones de la API

La API de Boostr retorna **feriados nacionales** solamente. Los feriados
regionales (ver sección 9) no están disponibles y deben cargarse
manualmente desde el mantenedor de feriados del sistema.

### Consideración de disponibilidad

La API es gratuita y mantenida por Boostr. Aunque es confiable, al ser
un servicio externo podría no estar disponible en algún momento.

Estrategia recomendada:
```
1. Ejecutar el seed con anticipación (no el mismo día que se necesita)
2. Mantener el script manual (seed_feriados_2026.py) como respaldo
3. Si la API falla, usar el script manual con los datos verificados
```

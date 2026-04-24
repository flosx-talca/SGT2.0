# SGT 2.1 — Roadmap completo, infraestructura y valor agregado

**Fecha:** Abril 2026
**Estado:** Documento de planificación estratégica

---

## 1. Infraestructura con contenedores

### 1.1 Stack recomendado

```
┌─────────────────────────────────────────────┐
│                   Nginx                      │  ← reverse proxy + SSL
│         (producción, opcional en dev)        │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │    Flask App         │  ← Gunicorn 4 workers
        │   python:3.12-slim   │
        └──────┬──────┬───────┘
               │      │
    ┌──────────▼─┐  ┌─▼──────────┐
    │ PostgreSQL  │  │   Redis     │
    │  16-alpine  │  │  7-alpine   │
    └────────────┘  └────────────┘
```

### 1.2 `docker-compose.yml`

```yaml
version: '3.9'

services:

  app:
    build: .
    container_name: sgt_app
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://sgt:sgt_pass@db:5432/sgt_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:16-alpine
    container_name: sgt_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: sgt
      POSTGRES_PASSWORD: sgt_pass
      POSTGRES_DB: sgt_db
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sgt -d sgt_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: sgt_redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Descomentar para producción:
  # nginx:
  #   image: nginx:alpine
  #   container_name: sgt_nginx
  #   ports:
  #     - "80:80"
  #     - "443:443"
  #   volumes:
  #     - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
  #     - ./nginx/ssl:/etc/nginx/ssl

volumes:
  pg_data:
  redis_data:
```

### 1.3 `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema (para psycopg2 y otros)
RUN apt-get update && apt-get install -y \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear directorio de logs
RUN mkdir -p /app/logs

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", \
     "--timeout", "120", "--log-level", "info", "run:app"]
```

### 1.4 `requirements.txt` actualizado

```
flask>=3.0
flask-sqlalchemy>=3.1
flask-migrate>=4.0
flask-login>=0.6          # ← autenticación
flask-session>=0.8        # ← sesiones en Redis
redis>=5.0                # ← cliente Redis
psycopg2-binary>=2.9      # ← PostgreSQL driver
gunicorn>=21.0            # ← servidor WSGI
ortools>=9.8              # ← motor CP-SAT
werkzeug>=3.0             # ← hashing de passwords
openpyxl>=3.1             # ← exportar Excel
reportlab>=4.0            # ← exportar PDF
requests>=2.31            # ← API Boostr feriados
python-dotenv>=1.0        # ← variables de entorno
```

### 1.5 Configuración Redis en Flask

```python
# app/config.py
import os

class Config:
    SECRET_KEY          = os.environ.get('SECRET_KEY', 'dev-key-cambiar-en-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Session con Redis
    SESSION_TYPE        = 'redis'
    SESSION_REDIS       = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    SESSION_PERMANENT   = True
    SESSION_USE_SIGNER  = True    # firma la cookie para seguridad
    PERMANENT_SESSION_LIFETIME = 86400 * 7   # 7 días

    # Flask-Login
    LOGIN_VIEW          = 'auth.login'
    LOGIN_MESSAGE       = 'Debes iniciar sesión para acceder.'
```

```python
# app/__init__.py
from flask_session import Session
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    # Redis sessions
    Session(app)

    # Login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.auth import Usuario
        return Usuario.query.get(int(user_id))

    # Registrar blueprints...
    return app
```

### 1.6 Contexto de empresa en sesión

El usuario logueado guarda en su sesión Redis qué empresa está gestionando:

```python
# En la sesión Redis se guarda:
session['empresa_activa_id']   = 1
session['empresa_activa_nombre'] = 'Copec Estación Central'
session['rol']                 = 'Administrador'

# Helper para obtener el contexto en cualquier blueprint:
def get_empresa_activa():
    empresa_id = session.get('empresa_activa_id')
    if not empresa_id:
        abort(403)
    return empresa_id
```

---

## 2. Exportación del cuadrante

### 2.1 Exportar a Excel (con colores)

Librería: `openpyxl`

```python
# scheduler/export_excel.py

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def exportar_cuadrante_excel(planificacion, celdas, trabajadores, dias, turnos_info):
    """
    Genera un archivo Excel del cuadrante con los mismos colores del frontend.

    Args:
        planificacion: objeto Planificacion
        celdas:        dict { fecha: { worker_id: turno_abr } }
        trabajadores:  lista de dicts { id, nombre }
        dias:          lista de dicts { fecha, label, es_feriado, ... }
        turnos_info:   dict { abreviacion: { color, nombre } }

    Returns:
        BytesIO con el archivo Excel
    """
    from io import BytesIO
    import re

    wb = Workbook()
    ws = wb.active
    ws.title = f"Cuadrante {planificacion.mes:02d}/{planificacion.anio}"

    # ── Colores de turnos (hex sin #) ──────────────────────────────────────
    COLOR_LIBRE    = 'F8F9FA'
    COLOR_AUSENCIA = 'E9ECEF'
    COLOR_FERIADO  = 'FFF3CD'
    COLOR_DOMINGO  = 'FFE0E0'
    COLOR_HEADER   = '2C3E50'
    COLOR_SIN_RESOLVER = 'FFF0D0'

    def hex_fill(hex_color):
        return PatternFill('solid', fgColor=hex_color.lstrip('#'))

    border = Border(
        left=Side(style='thin', color='DEE2E6'),
        right=Side(style='thin', color='DEE2E6'),
        top=Side(style='thin', color='DEE2E6'),
        bottom=Side(style='thin', color='DEE2E6')
    )

    # ── Fila de encabezado — nombre empresa y mes ─────────────────────────
    ws.merge_cells(f'A1:{get_column_letter(len(dias)+1)}1')
    ws['A1'] = f"{planificacion.empresa.razon_social} — Cuadrante {planificacion.mes:02d}/{planificacion.anio}"
    ws['A1'].font = Font(bold=True, color='FFFFFF', size=12)
    ws['A1'].fill = hex_fill(COLOR_HEADER)
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25

    # ── Fila 2 — encabezados de días ──────────────────────────────────────
    ws['A2'] = 'Trabajador'
    ws['A2'].font = Font(bold=True, color='FFFFFF')
    ws['A2'].fill = hex_fill(COLOR_HEADER)
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.column_dimensions['A'].width = 22

    for col_idx, dia in enumerate(dias, start=2):
        col_letter = get_column_letter(col_idx)
        ws[f'{col_letter}2'] = dia['label']
        ws[f'{col_letter}2'].font = Font(bold=True, size=8, color='FFFFFF')
        ws[f'{col_letter}2'].fill = hex_fill(
            'FFB3B3' if dia.get('es_domingo') else
            'FFE8A0' if dia.get('es_feriado') else
            COLOR_HEADER
        )
        ws[f'{col_letter}2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[col_letter].width = 7
    ws.row_dimensions[2].height = 30

    # ── Filas de trabajadores ─────────────────────────────────────────────
    for row_idx, trab in enumerate(trabajadores, start=3):
        ws[f'A{row_idx}'] = trab['nombre']
        ws[f'A{row_idx}'].font = Font(size=9)
        ws[f'A{row_idx}'].alignment = Alignment(vertical='center')
        ws[f'A{row_idx}'].border = border

        for col_idx, dia in enumerate(dias, start=2):
            col_letter = get_column_letter(col_idx)
            cell_ref   = f'{col_letter}{row_idx}'
            valor      = celdas.get(dia['fecha'], {}).get(trab['id'], '')

            ws[cell_ref] = valor
            ws[cell_ref].alignment = Alignment(horizontal='center', vertical='center')
            ws[cell_ref].font = Font(size=9, bold=bool(valor and valor not in ('L', '')))
            ws[cell_ref].border = border

            # Color según tipo de celda
            if not valor:                          # sin resolver
                fill_color = COLOR_SIN_RESOLVER
            elif valor == 'L':                     # libre
                fill_color = COLOR_LIBRE
            elif valor in ('VAC','LM','LT','P'):   # ausencia
                fill_color = COLOR_AUSENCIA
            elif dia.get('es_feriado'):            # feriado
                fill_color = turnos_info.get(valor, {}).get('color', 'FFFFFF')
                ws[cell_ref].font = Font(size=9, bold=True)
            else:                                  # turno normal
                fill_color = turnos_info.get(valor, {}).get('color', 'FFFFFF')

            ws[cell_ref].fill = hex_fill(fill_color)
        ws.row_dimensions[row_idx].height = 20

    # ── Leyenda de turnos ─────────────────────────────────────────────────
    leyenda_row = len(trabajadores) + 4
    ws[f'A{leyenda_row}'] = 'Leyenda:'
    ws[f'A{leyenda_row}'].font = Font(bold=True)
    for i, (abr, info) in enumerate(turnos_info.items()):
        col = get_column_letter(i + 2)
        ws[f'{col}{leyenda_row}'] = f"{abr} = {info.get('nombre', abr)}"
        ws[f'{col}{leyenda_row}'].fill = hex_fill(info.get('color', 'FFFFFF'))
        ws[f'{col}{leyenda_row}'].font = Font(size=8)
        ws[f'{col}{leyenda_row}'].alignment = Alignment(horizontal='center')

    # Freeze panes: fijar nombre trabajador y encabezado
    ws.freeze_panes = 'B3'

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
```

### 2.2 Exportar a PDF (con colores)

Librería: `reportlab`

```python
# scheduler/export_pdf.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from io import BytesIO

def exportar_cuadrante_pdf(planificacion, celdas, trabajadores, dias, turnos_info):
    """
    Genera un PDF del cuadrante con los mismos colores del frontend.
    Usa orientación horizontal para acomodar todos los días del mes.
    """

    output = BytesIO()
    doc    = SimpleDocTemplate(output, pagesize=landscape(A4),
                               leftMargin=1*cm, rightMargin=1*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles  = getSampleStyleSheet()
    story   = []

    # ── Título ────────────────────────────────────────────────────────────
    titulo = Paragraph(
        f"<b>{planificacion.empresa.razon_social}</b> — "
        f"Cuadrante {planificacion.mes:02d}/{planificacion.anio}",
        styles['Title']
    )
    story.append(titulo)
    story.append(Spacer(1, 0.3*cm))

    # ── Construir tabla ───────────────────────────────────────────────────
    def hex_to_color(hex_str):
        h = hex_str.lstrip('#')
        return colors.HexColor(f'#{h}')

    COLOR_HEADER   = '#2C3E50'
    COLOR_LIBRE    = '#F8F9FA'
    COLOR_AUSENCIA = '#E9ECEF'
    COLOR_DOMINGO  = '#FFE0E0'
    COLOR_FERIADO  = '#FFF3CD'
    COLOR_SIN_RESOL = '#FFF0D0'

    # Encabezado
    header = ['Trabajador'] + [d['label'] for d in dias]
    data   = [header]

    for trab in trabajadores:
        fila = [trab['nombre']]
        for dia in dias:
            valor = celdas.get(dia['fecha'], {}).get(trab['id'], '')
            fila.append(valor or '')
        data.append(fila)

    # Ancho de columnas: nombre más ancho, días más angostos
    n_dias  = len(dias)
    ancho_pagina = 27*cm   # landscape A4 usable
    ancho_nombre = 3.5*cm
    ancho_dia    = (ancho_pagina - ancho_nombre) / n_dias
    col_widths   = [ancho_nombre] + [ancho_dia] * n_dias

    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Estilo base
    style_cmds = [
        ('BACKGROUND',   (0,0), (-1,0),  hex_to_color(COLOR_HEADER)),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0),  6),
        ('FONTSIZE',     (0,1), (0,-1),  7),
        ('FONTSIZE',     (1,1), (-1,-1), 6),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWHEIGHT',    (0,0), (-1,-1), 14),
        ('GRID',         (0,0), (-1,-1), 0.25, colors.HexColor('#DEE2E6')),
        ('FONTNAME',     (0,1), (0,-1),  'Helvetica'),
        ('ALIGN',        (0,1), (0,-1),  'LEFT'),
    ]

    # Colorear celdas según valor y tipo de día
    for row_idx, trab in enumerate(trabajadores, start=1):
        for col_idx, dia in enumerate(dias, start=1):
            valor = celdas.get(dia['fecha'], {}).get(trab['id'], '')

            if not valor:
                bg = COLOR_SIN_RESOL
            elif valor == 'L':
                bg = COLOR_LIBRE
            elif valor in ('VAC', 'LM', 'LT', 'P'):
                bg = COLOR_AUSENCIA
            elif dia.get('es_domingo'):
                bg = turnos_info.get(valor, {}).get('color', COLOR_DOMINGO)
            elif dia.get('es_feriado'):
                bg = COLOR_FERIADO
            else:
                bg = turnos_info.get(valor, {}).get('color', '#FFFFFF')

            if bg != '#FFFFFF':
                style_cmds.append(
                    ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), hex_to_color(bg))
                )

        # Alternar color de fondo en filas de trabajadores
        if row_idx % 2 == 0:
            style_cmds.append(
                ('BACKGROUND', (0, row_idx), (0, row_idx), colors.HexColor('#F2F4F6'))
            )

    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    # ── Leyenda ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    leyenda_data = [['Leyenda:'] + [
        f"{abr} = {info.get('nombre', abr)}"
        for abr, info in turnos_info.items()
    ] + ['L = Libre', 'VAC = Vacaciones']]

    leyenda_table = Table(leyenda_data)
    leyenda_style = [
        ('FONTSIZE',  (0,0), (-1,-1), 7),
        ('FONTNAME',  (0,0), (0,0),   'Helvetica-Bold'),
        ('ALIGN',     (0,0), (-1,-1), 'CENTER'),
        ('GRID',      (0,0), (-1,-1), 0.25, colors.grey),
    ]
    for i, (abr, info) in enumerate(turnos_info.items(), start=1):
        leyenda_style.append(
            ('BACKGROUND', (i,0), (i,0), hex_to_color(info.get('color','#FFFFFF')))
        )
    leyenda_table.setStyle(TableStyle(leyenda_style))
    story.append(leyenda_table)

    doc.build(story)
    output.seek(0)
    return output
```

### 2.3 Endpoints de exportación

```python
# En planificacion_bp.py

@planificacion_bp.route('/exportar/excel/<int:planificacion_id>')
@login_required
def exportar_excel(planificacion_id):
    from app.scheduler.export_excel import exportar_cuadrante_excel
    plan = Planificacion.query.get_or_404(planificacion_id)
    # ... preparar datos ...
    output = exportar_cuadrante_excel(plan, celdas, trabajadores, dias, turnos_info)
    filename = f"cuadrante_{plan.anio}_{plan.mes:02d}_{plan.empresa.razon_social}.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@planificacion_bp.route('/exportar/pdf/<int:planificacion_id>')
@login_required
def exportar_pdf(planificacion_id):
    from app.scheduler.export_pdf import exportar_cuadrante_pdf
    plan = Planificacion.query.get_or_404(planificacion_id)
    # ... preparar datos ...
    output = exportar_cuadrante_pdf(plan, celdas, trabajadores, dias, turnos_info)
    filename = f"cuadrante_{plan.anio}_{plan.mes:02d}.pdf"
    return send_file(output, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)
```

---

## 3. Valor agregado — más allá de generar turnos

### 3.1 Gestión de compensatorios

Cada vez que un trabajador trabaja domingo o feriado, el sistema genera
automáticamente un compensatorio pendiente. El administrador asigna la
fecha de descanso compensatorio.

```
Flujo:
  Publicar cuadrante
    → detectar domingos/feriados trabajados
    → crear Compensatorio (estado='pendiente')
    → notificar al administrador

  Administrador asigna fecha compensatoria
    → esa fecha queda como BLOQUEADO en siguiente planificación
    → estado='asignado'

  Trabajador toma el día
    → estado='tomado'

  Finiquito
    → si no se tomó: estado='pagado_finiquito' con recargo
```

### 3.2 Panel de horas y liquidación

Con las horas calculadas por tipo al publicar el cuadrante, puedes generar
un resumen mensual por trabajador listo para la liquidación de sueldo:

```
Trabajador: Ana González — Abril 2026

  Horas hábiles:        120h  × $X = $XXX
  Horas nocturnas:       40h  × $X × 1.3 = $XXX  (recargo nocturno)
  Horas domingo:         16h  → 2 compensatorios pendientes
  Horas feriado:          8h  → 1 compensatorio pendiente
  Horas irrenunciables:   0h
  Horas extra:            0h
  ─────────────────────────────
  Total a pagar:        $XXX
  Compensatorios nuevos: 3
```

Esto se exporta a Excel por empresa y mes, listo para el área de RRHH.

### 3.3 Alertas operativas automáticas

El sistema detecta y alerta situaciones críticas antes de que el administrador
las encuentre manualmente:

```
Alertas críticas (bloquean operación):
  🔴 Cobertura insuficiente para el turno N del martes 15
  🔴 Trabajador X no tiene horas configuradas → no puede planificar

Alertas de cumplimiento legal:
  🟡 Trabajador Y lleva 5 domingos sin día libre compensatorio
  🟡 Trabajador Z acumula 18 horas extra este mes sin autorización
  🟡 Vacaciones de Pepito vencen en 30 días sin usar

Alertas operativas:
  🔵 3 trabajadores con licencia médica la próxima semana
  🔵 El cuadrante de mayo aún no ha sido publicado (estamos en 25 abril)
```

### 3.4 Dashboard analítico por empresa

```
Vista mensual:
  ┌─────────────────────────────────────────┐
  │  Cobertura real vs planificada          │  gráfico de barras por día
  │  Ausencias del mes                      │  por tipo (vacaciones/licencia)
  │  Distribución de turnos                 │  % M / T / I / N
  │  Compensatorios pendientes              │  semáforo: ok / atención / crítico
  └─────────────────────────────────────────┘

Vista histórica (últimos 6 meses):
  │  Evolución del déficit de cobertura     │
  │  Ausentismo por trabajador              │
  │  Costo estimado de horas extra          │
  │  Tendencia de licencias médicas         │
```

### 3.5 Portal del trabajador (PWA mobile)

Vista simplificada para que cada trabajador consulte su propio cuadrante
desde el celular, sin necesidad de que el administrador lo imprima:

```
Trabajador ve:
  ✅ Su cuadrante del mes actual y siguiente
  ✅ Sus días libres y turnos asignados
  ✅ Sus compensatorios pendientes
  ✅ Sus vacaciones registradas
  📱 Notificación push cuando se publica el cuadrante
  📱 Notificación si le asignan un turno manual

Trabajador NO puede:
  ❌ Ver cuadrante de otros trabajadores
  ❌ Modificar nada
```

### 3.6 Solicitudes de cambio de turno

Trabajadores pueden solicitar cambios que el administrador aprueba o rechaza:

```
Flujo:
  Trabajador solicita: "No puedo trabajar el martes 15"
    → sistema busca automáticamente reemplazante disponible
    → propone intercambio con otro trabajador
    → administrador aprueba/rechaza
    → cuadrante se actualiza si es aprobado
    → ambos reciben notificación
```

### 3.7 Planificación multi-mes (vista anual)

Vista que muestra los 12 meses del año con semáforos de estado:

```
Empresa: Copec Estación Central

Ene  Feb  Mar  Abr  May  Jun  Jul  Ago  Sep  Oct  Nov  Dic
 ✅   ✅   ✅   ✅   ⏳   ⚪   ⚪   ⚪   ⚪   ⚪   ⚪   ⚪

✅ = Publicado y cerrado
⏳ = En simulación
⚪ = Sin generar
```

### 3.8 Reportes de cumplimiento legal

Documentos exportables que demuestran cumplimiento ante la Dirección del
Trabajo o una auditoría:

```
Reporte de descanso semanal:
  → Todos los trabajadores tuvieron al menos 1 día libre por semana ✅

Reporte de domingos:
  → Todos tuvieron al menos 2 domingos libres en el mes ✅
  → Domingos trabajados con compensatorio asignado ✅

Reporte de jornada:
  → Ningún trabajador superó las 42h semanales ✅
  → Detalle de semanas donde se acercó al límite
```

---

## 4. Features completo — tabla priorizada

### Prioridad CRÍTICA — sin esto el sistema no funciona en producción

| # | Feature | Sprint |
|---|---|---|
| C1 | Docker Compose (app + db + redis) | 1 |
| C2 | Flask-Login + autenticación | 1 |
| C3 | Redis para sesiones | 1 |
| C4 | Filtrado de datos por empresa activa | 1 |
| C5 | Menú dinámico por rol desde BD | 1 |
| C6 | Persistencia cuadrante (Planificacion + Cuadrante) | 2 |
| C7 | Endpoint /publicar con cálculo de horas | 2 |
| C8 | Edición manual cuadrante con auditoría | 2 |

### Prioridad ALTA — valor diferencial del producto

| # | Feature | Sprint |
|---|---|---|
| A1 | Exportar cuadrante a Excel con colores | 3 |
| A2 | Exportar cuadrante a PDF con colores | 3 |
| A3 | Gestión de compensatorios | 3 |
| A4 | Dashboard analítico con datos reales | 3 |
| A5 | Alertas operativas automáticas | 4 |
| A6 | Panel de horas para liquidación (Excel) | 4 |
| A7 | Contexto mes anterior en builder | 4 |
| A8 | Seed feriados desde API Boostr | 4 |

### Prioridad MEDIA — madurez del sistema

| # | Feature | Sprint |
|---|---|---|
| M1 | Sistema de reglas dinámicas desde BD | 5 |
| M2 | Reportes de cumplimiento legal (PDF) | 5 |
| M3 | Chequeo de dotación previo a generar | 5 |
| M4 | Planificación multi-mes (vista anual) | 5 |
| M5 | Restricciones por fecha específica | 6 |
| M6 | Feriados regionales (UniqueConstraint) | 6 |
| M7 | Quinto domingo (manejo especial) | 6 |
| M8 | Horas extra por trabajador (campo BD) | 6 |

### Prioridad BAJA — diferenciación y retención

| # | Feature | Sprint |
|---|---|---|
| B1 | Portal del trabajador (PWA mobile) | 7 |
| B2 | Solicitudes de cambio de turno | 7 |
| B3 | Notificaciones push (cuadrante publicado) | 7 |
| B4 | Planificación asistida IA (sugerencias) | 8 |
| B5 | Integración con sistemas de RRHH (API) | 8 |
| B6 | App móvil nativa | 9 |

---

## 5. Sprints detallados

```
Sprint 1 (2 semanas) — Infraestructura base
  C1: Docker Compose + Dockerfile + redis + postgres
  C2: Flask-Login con roles (Super Admin, Cliente, Admin)
  C3: Flask-Session con Redis
  C4: Filtrado queries por empresa activa en sesión
  C5: Menú dinámico (seed roles/menus/rolmenu)

Sprint 2 (2 semanas) — Cuadrante persistente
  C6: Migración Planificacion + Cuadrante
  C7: Endpoint /publicar + cálculo horas
  C8: Edición manual + flag omite_validacion

Sprint 3 (2 semanas) — Exportación + Compensatorios
  A1: Export Excel con openpyxl + colores
  A2: Export PDF con reportlab + colores
  A3: Gestión compensatorios (tabla + flujo)
  A4: Dashboard con KPIs reales desde BD

Sprint 4 (2 semanas) — Alertas y operación
  A5: Alertas automáticas (cobertura, legal, vencimientos)
  A6: Panel horas para liquidación
  A7: Builder considera días consecutivos mes anterior
  A8: Comando flask seed-feriados desde API Boostr
```

---

## 6. Feature: Alerta de capacidad en tiempo real

**Prioridad:** ALTA — feature rápido de implementar, alto valor comercial

### El problema que resuelve

Sin esta alerta, el administrador descubre que el cuadrante no se puede
cumplir DESPUÉS de generarlo (solver retorna INFEASIBLE o con déficit).
Con la alerta, lo sabe en el momento en que registra la ausencia.

### Cómo funciona

```
Cada vez que se registra o modifica una ausencia, el sistema recalcula:

  capacidad_disponible = sum(
      ceil(dias_disponibles_w / 7 * horas_w / duracion_turno)
      para cada trabajador
      donde dias_disponibles_w = dias_mes - ausencias_w - domingos_libres_min
  )

  turnos_necesarios = sum(dotacion_turno * dias_mes para cada turno)

  Si capacidad_disponible < turnos_necesarios:
      → ALERTA ROJA: "Esta ausencia genera déficit de X turnos en el mes"
      → Mostrar qué turnos específicos quedarían descubiertos
```

### Implementación rápida (función Python)

```python
# controllers/ausencia_utils.py

import math

def calcular_capacidad_mes(empresa_id, mes, anio, ausencias_nuevas=None):
    """
    Calcula la capacidad vs dotación requerida para un mes.
    ausencias_nuevas: lista de ausencias aún no guardadas para simular el impacto.

    Retorna dict con estado del semáforo.
    """
    from calendar import monthrange
    from app.models.business import Trabajador, Turno

    dias_mes    = monthrange(anio, mes)[1]
    domingos    = sum(1 for d in range(1, dias_mes+1)
                      if date(anio, mes, d).weekday() == 6)
    libres_min  = 2   # ley: mínimo 2 domingos libres

    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).all()
    turnos       = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()

    # Calcular ausencias del mes (incluyendo las nuevas a simular)
    ausencias_por_trabajador = {}  # { worker_id: dias_de_ausencia }
    for t in trabajadores:
        dias_aus = 0
        for a in t.ausencias:
            # contar días que caen en el mes
            curr = max(a.fecha_inicio, date(anio, mes, 1))
            fin  = min(a.fecha_fin, date(anio, mes, dias_mes))
            if curr <= fin:
                dias_aus += (fin - curr).days + 1
        ausencias_por_trabajador[t.id] = dias_aus

    # Agregar ausencias nuevas (simulación antes de guardar)
    if ausencias_nuevas:
        for aus in ausencias_nuevas:
            ausencias_por_trabajador[aus['trabajador_id']] = \
                ausencias_por_trabajador.get(aus['trabajador_id'], 0) + aus['dias']

    # Calcular capacidad total
    capacidad_total = 0
    for t in trabajadores:
        dias_bloq     = ausencias_por_trabajador.get(t.id, 0)
        dias_dom_libr = libres_min
        dias_disponib = dias_mes - dias_bloq - dias_dom_libr
        if dias_disponib <= 0:
            continue
        turnos_semana = t.horas_semanales / 8   # duracion default 8h
        meta          = math.ceil(dias_disponib / 7 * turnos_semana)
        capacidad_total += meta

    # Calcular dotación requerida
    dotacion_total = sum(t.dotacion_diaria * dias_mes for t in turnos)

    deficit  = dotacion_total - capacidad_total
    superavit = capacidad_total - dotacion_total

    return {
        'capacidad':   capacidad_total,
        'necesarios':  dotacion_total,
        'deficit':     max(0, deficit),
        'superavit':   max(0, superavit),
        'estado':      'critico' if deficit > 0 else
                       'atencion' if superavit < dotacion_total * 0.05 else
                       'ok',
        'mensaje':     f'Faltan {deficit} turnos-persona para cubrir el mes' if deficit > 0 else
                       f'Capacidad OK — sobran {superavit} turnos-persona'
    }
```

### En el endpoint de guardar ausencia

```python
# Antes de guardar, simular impacto:
@trabajador_bp.route('/ausencia/guardar', methods=['POST'])
@login_required
def guardar_ausencia():
    ...
    # Simular el impacto ANTES de guardar
    impacto = calcular_capacidad_mes(
        empresa_id=empresa_id,
        mes=mes_afectado,
        anio=anio_afectado,
        ausencias_nuevas=[{'trabajador_id': tid, 'dias': dias_ausencia}]
    )

    # Guardar la ausencia
    ...

    # Retornar con alerta si corresponde
    respuesta = {'ok': True, 'msg': 'Ausencia registrada.'}
    if impacto['estado'] == 'critico':
        respuesta['alerta'] = {
            'tipo':    'danger',
            'mensaje': f"⚠️ {impacto['mensaje']}. El cuadrante de {mes}/{anio} "
                       f"podría no cumplirse con la dotación actual."
        }
    elif impacto['estado'] == 'atencion':
        respuesta['alerta'] = {
            'tipo':    'warning',
            'mensaje': f"Atención: {impacto['mensaje']}. Margen muy ajustado."
        }

    return jsonify(respuesta)
```

### En el frontend — semáforo permanente

En la pantalla de ausencias y en el dashboard, mostrar el semáforo siempre:

```html
<!-- Semáforo de capacidad del mes -->
<div class="card border-0 shadow-sm">
  <div class="card-body d-flex align-items-center gap-3">
    <div id="semaforo-capacidad" class="rounded-circle"
         style="width:20px;height:20px;background:#2ecc71"></div>
    <div>
      <small class="text-muted fw-bold text-uppercase">Capacidad Mayo 2026</small>
      <p class="mb-0 fw-bold" id="texto-capacidad">260 disponibles / 240 necesarios</p>
    </div>
  </div>
</div>
```

---

## 7. Pantalla de ausencias separada

### Por qué separarla del mantenedor del trabajador

| | Dentro del trabajador (hoy) | Pantalla separada |
|---|---|---|
| Registrar ausencia | Buscar trabajador → abrir modal → sección ausencias | Directo desde menú |
| Ver ausencias del mes | Imposible (una por una) | Calendario visual completo |
| Alerta de capacidad | Solo al guardar, sin contexto | Semáforo siempre visible |
| Gestión masiva | Imposible | Filtrar por empresa/mes/tipo |

### Lo que incluiría la pantalla

```
Pantalla: Gestión de Ausencias

Filtros:  [Empresa ▼]  [Mes ▼]  [Año ▼]  [Tipo ▼]  [Buscar trabajador]

Semáforo: 🟢 Capacidad OK — 260 disponibles / 240 necesarios

Vista calendario:
  [Lun 1][Mar 2][Mié 3][Jue 4][Vie 5][Sáb 6][Dom 7]
  Ana  → ████ VAC ████
  Pedro→              ████ LM ████████

Vista lista:
  Ana González    VAC   01/05 → 07/05  (7 días)  [Editar][Eliminar]
  Pedro Rojas     LM    05/05 → 15/05  (11 días) [Editar][Eliminar]

[+ Nueva Ausencia]
```

### Lo que se queda en el mantenedor del trabajador

```
Mantenedor trabajador mantiene:
  ✅ Datos personales y contrato
  ✅ Patrones de turno por día de semana (preferencias permanentes)
  ✅ Historial de ausencias (solo lectura, link a la pantalla de ausencias)

Se mueve a pantalla separada:
  → Crear/editar ausencias del mes
  → Vista calendar de ausencias
  → Alerta de impacto en dotación
```

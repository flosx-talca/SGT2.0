# SGT 2.1 — Parte 8: Mantenedor Unificado de Restricciones del Trabajador

## Contexto

`TipoAusencia` y `TrabajadorAusencia` ya existen y funcionan en BD.
`TrabajadorRestriccionTurno` es nueva (ver Parte 1).

El objetivo es unificar ambas en **una sola pantalla** para el Admin,
manteniendo las dos tablas en BD pero añadiendo el campo `categoria`
a `TipoAusencia` para que el Builder sepa cómo tratar cada registro.

---

## 8.1 Nuevo Enum: `CategoriaAusencia`

```python
# app/models/enums.py — AGREGAR a los enums existentes

from enum import Enum

class CategoriaAusencia(str, Enum):
    AUSENCIA    = "ausencia"
    # → Bloquea el día completo en el Solver (Hard)
    # → Ejemplos: vacaciones, licencia, permiso con/sin goce, compensatorio

    RESTRICCION = "restriccion"
    # → Restringe un turno específico (Hard o Soft según tipo)
    # → Ejemplos: turno fijo, excluir turno, preferente, post_noche
```

---

## 8.2 Modificación en `TipoAusencia`

```python
# app/models/business.py — MODIFICAR modelo existente

class TipoAusencia(db.Model):
    __tablename__ = "tipo_ausencia"
    id             = db.Column(db.Integer, primary_key=True)
    empresa_id     = db.Column(db.Integer, db.ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    nombre         = db.Column(db.String(50),  nullable=False)
    abreviacion    = db.Column(db.String(5),   nullable=False)
    color          = db.Column(db.String(10),  default="#95a5a6")

    # ── CAMPO NUEVO ──────────────────────────────────────────────────────
    categoria      = db.Column(
        db.Enum(CategoriaAusencia),
        nullable=False,
        default=CategoriaAusencia.AUSENCIA
    )
    # AUSENCIA    → bloquea día completo en el Solver
    # RESTRICCION → restringe turno específico (usa TrabajadorRestriccionTurno)

    # ── CAMPO NUEVO ──────────────────────────────────────────────────────
    tipo_restriccion = db.Column(db.String(30), nullable=True)
    # Solo aplica si categoria == RESTRICCION
    # Valores válidos: "excluir_turno", "solo_turno", "turno_fijo",
    #                  "turno_preferente", "post_noche"
    # None si categoria == AUSENCIA

    activo         = db.Column(db.Boolean,    default=True)
    creado_en      = db.Column(db.DateTime,   default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime,   default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa        = db.relationship("Empresa", backref=db.backref("tipos_ausencia", lazy=True))
```

---

## 8.3 Migración

```bash
flask db migrate -m "add_categoria_tipo_restriccion_to_tipo_ausencia"
flask db upgrade
```

La migración solo agrega dos columnas nuevas. No toca datos existentes.
Los registros existentes quedarán con `categoria = NULL` → actualizar con el seed.

```python
# Script de actualización post-migración para registros existentes
# Ejecutar UNA VEZ en flask shell

from app.models.business import TipoAusencia
from app.models.enums import CategoriaAusencia
from app.database import db

# Todos los existentes son ausencias (vacaciones, licencias, permisos)
TipoAusencia.query.update({"categoria": CategoriaAusencia.AUSENCIA})
db.session.commit()
print("OK — tipos existentes actualizados a categoría AUSENCIA")
```

---

## 8.4 Seed de tipos base

```python
# app/seeds/tipos_ausencia_base.py

from app.models.business import TipoAusencia
from app.models.enums import CategoriaAusencia
from app.database import db

TIPOS_BASE = [
    # nombre,                abrev,   color,      categoria,                    tipo_restriccion
    ("Vacaciones",           "VAC",   "#3498db",  CategoriaAusencia.AUSENCIA,    None),
    ("Licencia médica",      "LM",    "#e74c3c",  CategoriaAusencia.AUSENCIA,    None),
    ("Permiso con goce",     "PCG",   "#f39c12",  CategoriaAusencia.AUSENCIA,    None),
    ("Permiso sin goce",     "PSG",   "#95a5a6",  CategoriaAusencia.AUSENCIA,    None),
    ("Día compensatorio",    "COMP",  "#9b59b6",  CategoriaAusencia.AUSENCIA,    None),
    ("Turno fijo",           "TF",    "#27ae60",  CategoriaAusencia.RESTRICCION, "turno_fijo"),
    ("Excluir turno",        "ET",    "#c0392b",  CategoriaAusencia.RESTRICCION, "excluir_turno"),
    ("Solo turno",           "ST",    "#2980b9",  CategoriaAusencia.RESTRICCION, "solo_turno"),
    ("Turno preferente",     "TP",    "#f1c40f",  CategoriaAusencia.RESTRICCION, "turno_preferente"),
    ("Post noche libre",     "PNL",   "#1abc9c",  CategoriaAusencia.RESTRICCION, "post_noche"),
]


def seed_tipos_ausencia_base(empresa_id: int):
    """
    Inserta los tipos base para una empresa.
    Llamar al crear una empresa nueva.
    """
    for nombre, abrev, color, categoria, tipo_restriccion in TIPOS_BASE:
        existe = TipoAusencia.query.filter_by(
            empresa_id=empresa_id,
            abreviacion=abrev
        ).first()
        if not existe:
            db.session.add(TipoAusencia(
                empresa_id=empresa_id,
                nombre=nombre,
                abreviacion=abrev,
                color=color,
                categoria=categoria,
                tipo_restriccion=tipo_restriccion
            ))
    db.session.commit()
```

---

## 8.5 Modificación en `TrabajadorAusencia`

No se modifica la estructura. Solo se agrega una propiedad calculada para el Builder:

```python
# app/models/business.py — AGREGAR propiedad a TrabajadorAusencia

class TrabajadorAusencia(db.Model):
    __tablename__ = "trabajador_ausencia"
    id               = db.Column(db.Integer, primary_key=True)
    trabajador_id    = db.Column(db.Integer, db.ForeignKey("trabajador.id", ondelete="CASCADE"), nullable=False)
    fecha_inicio     = db.Column(db.Date,    nullable=False)
    fecha_fin        = db.Column(db.Date,    nullable=False)
    motivo           = db.Column(db.String(255), nullable=False, default="")
    tipo_ausencia_id = db.Column(db.Integer, db.ForeignKey("tipo_ausencia.id", ondelete="CASCADE"), nullable=True)
    tipo_ausencia    = db.relationship("TipoAusencia", lazy=True)
    creado_en        = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def es_bloqueo_dia(self) -> bool:
        """True si bloquea el día completo (categoría AUSENCIA)."""
        if self.tipo_ausencia is None:
            return True  # sin tipo → bloquear por seguridad
        return self.tipo_ausencia.categoria == CategoriaAusencia.AUSENCIA

    @property
    def es_restriccion_turno(self) -> bool:
        """True si es una restricción de turno específica."""
        if self.tipo_ausencia is None:
            return False
        return self.tipo_ausencia.categoria == CategoriaAusencia.RESTRICCION

    @property
    def tipo_restriccion(self) -> str | None:
        """Retorna el tipo de restricción si aplica."""
        if self.tipo_ausencia is None:
            return None
        return self.tipo_ausencia.tipo_restriccion
```

---

## 8.6 Relación con `TrabajadorRestriccionTurno`

Cuando el Admin registra una ausencia de categoría `RESTRICCION` en el mantenedor,
el backend **crea automáticamente** un registro en `TrabajadorRestriccionTurno`:

```python
# app/routes/trabajador_bp.py (o service equivalente)

@trabajador_bp.route("/trabajadores/<int:tid>/ausencias", methods=["POST"])
def crear_ausencia(tid):
    data = request.get_json()
    tipo = TipoAusencia.query.get_or_404(data["tipo_ausencia_id"])

    # 1. Crear siempre el registro de ausencia
    ausencia = TrabajadorAusencia(
        trabajador_id    = tid,
        fecha_inicio     = data["fecha_inicio"],
        fecha_fin        = data["fecha_fin"],
        motivo           = data.get("motivo", ""),
        tipo_ausencia_id = tipo.id
    )
    db.session.add(ausencia)

    # 2. Si es RESTRICCION → crear también en TrabajadorRestriccionTurno
    if tipo.categoria == CategoriaAusencia.RESTRICCION:
        restriccion = TrabajadorRestriccionTurno(
            trabajador_id = tid,
            empresa_id    = data["empresa_id"],
            tipo          = tipo.tipo_restriccion,
            naturaleza    = NATURALEZA_POR_TIPO[tipo.tipo_restriccion],
            fecha_inicio  = data["fecha_inicio"],
            fecha_fin     = data["fecha_fin"],
            dias_semana   = data.get("dias_semana"),      # lista [0-6] o None
            turno_id      = data.get("turno_id"),
            motivo        = data.get("motivo", "")
        )
        db.session.add(restriccion)

    db.session.commit()
    return jsonify({"status": "ok"}), 201
```

De esta forma el Admin trabaja con **una sola pantalla** y el sistema mantiene
ambas tablas sincronizadas automáticamente.

---

## 8.7 Consumo en el Builder

```python
# app/scheduler/builder.py

# ── Paso 1: Pre-calcular días bloqueados (categoria AUSENCIA) ────────
dias_bloqueados = {}

for w in workers:
    bloqueados = set()
    ausencias  = TrabajadorAusencia.query.filter(
        TrabajadorAusencia.trabajador_id == w.id,
        TrabajadorAusencia.fecha_inicio  <= fecha_fin,
        TrabajadorAusencia.fecha_fin     >= fecha_inicio
    ).all()

    for aus in ausencias:
        if aus.es_bloqueo_dia:                      # ← usa la propiedad
            d = max(aus.fecha_inicio, fecha_inicio)
            while d <= min(aus.fecha_fin, fecha_fin):
                bloqueados.add(d)
                d += timedelta(days=1)

    dias_bloqueados[w.id] = bloqueados

# ── Paso 2: Aplicar bloqueos como Hard constraint ────────────────────
for w in workers:
    for d in dias_bloqueados[w.id]:
        for t in shifts:
            model.Add(x[w.id, d, t.id] == 0)

# ── Paso 3: Aplicar restricciones de turno ───────────────────────────
# (TrabajadorRestriccionTurno — ya creadas automáticamente por el backend)
restricciones = TrabajadorRestriccionTurno.query.filter_by(
    activo=True
).filter(
    TrabajadorRestriccionTurno.fecha_inicio <= fecha_fin,
    TrabajadorRestriccionTurno.fecha_fin    >= fecha_inicio
).all()

for r in restricciones:
    dias_aplica = [
        d for d in days
        if r.fecha_inicio <= d <= r.fecha_fin
        and (r.dias_semana is None or d.weekday() in r.dias_semana)
        and d not in dias_bloqueados[r.trabajador_id]  # no pisarse con ausencias
    ]

    if r.tipo == "excluir_turno":
        for d in dias_aplica:
            model.Add(x[r.trabajador_id, d, r.turno_id] == 0)

    elif r.tipo in ("solo_turno", "turno_fijo"):
        for d in dias_aplica:
            model.Add(x[r.trabajador_id, d, r.turno_id] == 1)
            for t_otro in shifts:
                if t_otro.id != r.turno_id:
                    model.Add(x[r.trabajador_id, d, t_otro.id] == 0)

    elif r.tipo == "post_noche":
        for i, d in enumerate(dias_aplica[:-1]):
            d_sig = dias_aplica[i + 1]
            turno_noche_ids = [t.id for t in shifts if t.es_nocturno]
            hizo_noche = x[r.trabajador_id, d, r.turno_id]
            hace_noche_sig = model.NewBoolVar(f"noche_sig_{r.trabajador_id}_{i}")
            model.Add(
                sum(x[r.trabajador_id, d_sig, tn] for tn in turno_noche_ids) >= 1
            ).OnlyEnforceIf(hace_noche_sig)
            model.Add(
                sum(x[r.trabajador_id, d_sig, tn] for tn in turno_noche_ids) == 0
            ).OnlyEnforceIf(hace_noche_sig.Not())
            dia_libre = 1 - sum(x[r.trabajador_id, d_sig, t.id] for t in shifts)
            model.Add(dia_libre == 1).OnlyEnforceIf([hizo_noche, hace_noche_sig.Not()])

    elif r.tipo == "turno_preferente":
        for d in dias_aplica:
            penalty = ConfigManager.get_int("SOFT_PENALTY_DIA_AISLADO", 100)
            objective_terms.append(
                penalty * (1 - x[r.trabajador_id, d, r.turno_id])
            )
```

---

## 8.8 Validación previa al Solver

```python
# app/services/scheduling_service.py

def validar_cobertura_factible(workers, shifts, days, dias_bloqueados) -> list[dict]:
    """
    Detecta días donde las ausencias dejan cobertura imposible.
    Ejecutar ANTES del Solver para alertar al Admin.
    """
    alertas = []
    for d in days:
        for t in shifts:
            disponibles = [
                w for w in workers
                if d not in dias_bloqueados[w.id]
            ]
            if len(disponibles) < t.dotacion_diaria:
                alertas.append({
                    "fecha":       d.strftime("%d/%m/%Y"),
                    "turno":       t.nombre,
                    "disponibles": len(disponibles),
                    "requeridos":  t.dotacion_diaria,
                    "faltantes":   t.dotacion_diaria - len(disponibles)
                })
    return alertas
```

---

## 8.9 Diseño del mantenedor en UI

### Vista principal del trabajador

```
┌─────────────────────────────────────────────────────────┐
│ Restricciones de Juan Pérez          [+ Agregar]        │
├──────────────┬────────────┬────────────┬────────────────┤
│ Tipo         │ Desde      │ Hasta      │ Detalle        │
├──────────────┼────────────┼────────────┼────────────────┤
│ 🏖️ Vacaciones│ 01/06/2025 │ 15/06/2025 │ —              │
│ 🏥 Lic. Méd │ 20/06/2025 │ 25/06/2025 │ —              │
│ 🔒 Turno fijo│ 01/06/2025 │ 30/06/2025 │ Mañana·Lun-Vie │
│ ⭐ Preferente│ 01/06/2025 │ 30/06/2025 │ Tarde          │
│ 🚫 Excluir  │ 01/06/2025 │ 30/06/2025 │ Noche          │
└──────────────┴────────────┴────────────┴────────────────┘
```

### Modal "Agregar restricción" con campos dinámicos

```javascript
// Lógica del modal: mostrar/ocultar campos según categoría del tipo seleccionado

tipoSelect.addEventListener('change', function() {
    const categoria = this.options[this.selectedIndex].dataset.categoria;

    if (categoria === 'ausencia') {
        // Mostrar: fecha_inicio, fecha_fin, motivo (opcional)
        // Ocultar: turno_id, dias_semana
        campoTurno.classList.add('d-none');
        campoDias.classList.add('d-none');
        campoMotivo.classList.remove('d-none');
    }

    if (categoria === 'restriccion') {
        // Mostrar: fecha_inicio, fecha_fin, turno_id, dias_semana
        // Ocultar: motivo
        campoTurno.classList.remove('d-none');
        campoDias.classList.remove('d-none');
        campoMotivo.classList.add('d-none');
    }
});
```

---

## 8.10 Resumen de cambios

| Archivo | Acción | Detalle |
|---|---|---|
| `app/models/enums.py` | Agregar | `CategoriaAusencia` enum |
| `app/models/business.py` | Modificar | Agregar `categoria` y `tipo_restriccion` a `TipoAusencia` |
| `app/models/business.py` | Modificar | Agregar propiedades `es_bloqueo_dia`, `es_restriccion_turno` a `TrabajadorAusencia` |
| `app/seeds/tipos_ausencia_base.py` | Crear | Seed con 10 tipos base (5 ausencias + 5 restricciones) |
| `app/routes/trabajador_bp.py` | Modificar | Al crear ausencia de categoría RESTRICCION → crear también en `TrabajadorRestriccionTurno` |
| `app/scheduler/builder.py` | Modificar | Consumir `es_bloqueo_dia` para separar bloqueos de restricciones |
| `app/services/scheduling_service.py` | Modificar | Agregar `validar_cobertura_factible()` antes del Solver |
| Migración | Crear | `add_categoria_tipo_restriccion_to_tipo_ausencia` |

---

## 8.11 Checklist

```
□ Agregar CategoriaAusencia a app/models/enums.py
□ Agregar campos categoria y tipo_restriccion a TipoAusencia en business.py
□ Agregar propiedades es_bloqueo_dia y es_restriccion_turno a TrabajadorAusencia
□ flask db migrate -m "add_categoria_tipo_restriccion_to_tipo_ausencia"
□ flask db upgrade
□ Actualizar registros existentes → categoria = AUSENCIA
□ Crear app/seeds/tipos_ausencia_base.py y ejecutar seed por empresa
□ Modificar ruta POST ausencias → crear TrabajadorRestriccionTurno si categoria == RESTRICCION
□ Actualizar Builder → usar es_bloqueo_dia para separar bloqueos de restricciones
□ Agregar validar_cobertura_factible() antes de correr el Solver
□ Actualizar modal UI → campos dinámicos según categoría del tipo seleccionado
```

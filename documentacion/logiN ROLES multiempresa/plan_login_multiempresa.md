# SGT 2.1 — Implementación Login, Roles y Multiempresa

**Alcance:** Solo autenticación, roles, contexto multiempresa y menú dinámico.
**NO modifica:** builder.py, solver.py, explain.py, conflict.py, legal_engine.py,
                  config_manager.py, planificacion_bp.py ni ningún archivo del scheduler.

---

## ÍNDICE

1. [Qué hay que hacer](#1-qué-hay-que-hacer)
2. [Modelos nuevos y modificados](#2-modelos-nuevos-y-modificados)
3. [Migración de BD](#3-migración-de-bd)
4. [Archivos a modificar](#4-archivos-a-modificar)
5. [Archivos nuevos a crear](#5-archivos-nuevos-a-crear)
6. [Layout y menú dinámico](#6-layout-y-menú-dinámico)
7. [Seed de roles, menús y Super Admin](#7-seed-de-roles-menús-y-super-admin)
8. [Patrón estándar para blueprints](#8-patrón-estándar-para-blueprints)
9. [Plan de implementación paso a paso](#9-plan-de-implementación-paso-a-paso)
10. [Preparación para Redis](#10-preparación-para-redis)

---

## 1. Qué hay que hacer

### Estado actual
```
❌ No hay Flask-Login instalado
❌ No hay @login_required en ninguna ruta
❌ El login renderiza la página pero no valida ni crea sesión
❌ Menú hardcodeado en layout.html
❌ Todas las queries muestran datos de TODAS las empresas
❌ No hay tabla UsuarioEmpresa (admin no puede gestionar varias empresas)
❌ Usuario hardcodeado en layout.html ("M. Cordero / Administrador")
❌ Sucursales hardcodeadas en layout.html
```

### Estado objetivo
```
✅ Login real con email + password
✅ Sesión persistente con Flask-Login
✅ @login_required protege todas las rutas
✅ Menú lateral cargado desde BD según el rol del usuario
✅ Cada query filtrada por empresa_activa_id de la sesión
✅ Selector de empresa en el menú (cambia el contexto sin relogin)
✅ Super Admin ve todo, Cliente ve sus empresas, Admin ve las asignadas
✅ Al crear una empresa → turnos y tipos de ausencia base se crean solos
```

### Lo que NO cambia
```
✅ Builder y scheduler → sin tocar
✅ Lógica de generación del cuadrante → sin tocar
✅ planificacion_bp.py → solo agregar @login_required y empresa_id
✅ Modelos de Trabajador, Turno, Regla → sin cambios de lógica
```

---

## 2. Modelos nuevos y modificados

### 2.1 `auth.py` — cambios

**Usuario: agregar UserMixin y nuevos campos**

```python
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    # Campos existentes (sin cambios):
    id         = db.Column(db.Integer, primary_key=True)
    rut        = db.Column(db.String(15), nullable=False, unique=True)
    nombre     = db.Column(db.String(100), nullable=False)
    apellidos  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id     = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    activo     = db.Column(db.Boolean, default=True)

    # NUEVO: empresa activa en sesión persistida en BD
    empresa_activa_id = db.Column(db.Integer,
                                  db.ForeignKey('empresa.id', ondelete='SET NULL'),
                                  nullable=True)

    # Relaciones
    empresa_activa = db.relationship('Empresa',
                                     foreign_keys=[empresa_activa_id], lazy=True)
    empresas       = db.relationship('UsuarioEmpresa', backref='usuario',
                                     lazy=True, cascade='all, delete-orphan')

    # ── Métodos de seguridad ──────────────────────────────────────────────────
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ── Propiedades de rol ────────────────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.rol.descripcion == 'Super Admin'

    @property
    def is_cliente(self):
        return self.rol.descripcion == 'Cliente'

    @property
    def is_administrador(self):
        return self.rol.descripcion == 'Administrador'

    # Flask-Login requiere is_active (usa campo activo del modelo)
    @property
    def is_active(self):
        return self.activo
```

**Menu: agregar endpoint, icono, orden**

```python
class Menu(db.Model):
    __tablename__ = 'menu'

    # Campos existentes:
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    activo      = db.Column(db.Boolean, default=True)

    # NUEVOS: necesarios para el menú dinámico
    endpoint    = db.Column(db.String(100))  # nombre de ruta Flask: 'trabajador.index'
    icono       = db.Column(db.String(50))   # clase Font Awesome: 'fa-users'
    orden       = db.Column(db.Integer, default=0)
```

### 2.2 `auth.py` — tabla nueva `UsuarioEmpresa`

Permite que un Administrador gestione múltiples empresas:

```python
class UsuarioEmpresa(db.Model):
    """
    Relación many-to-many entre Usuario y Empresa.

    Reglas:
    - Super Admin: NO necesita registros aquí (ve todo)
    - Cliente: sus empresas via cliente_id en Usuario
    - Administrador: SOLO las empresas en esta tabla
    """
    __tablename__ = 'usuario_empresa'
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'empresa_id',
                            name='uq_usuario_empresa'),
    )
    id         = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer,
                           db.ForeignKey('usuario.id', ondelete='CASCADE'),
                           nullable=False)
    empresa_id = db.Column(db.Integer,
                           db.ForeignKey('empresa.id', ondelete='CASCADE'),
                           nullable=False)
    activo     = db.Column(db.Boolean, default=True)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow)
```

### 2.3 `business.py` — tabla nueva `TurnoPlantilla`

Plantillas globales que se copian al crear una empresa:

```python
class TurnoPlantilla(db.Model):
    """
    Plantillas globales de turno. Sin empresa_id.
    Al crear una Empresa, se copian como Turno con empresa_id.
    """
    __tablename__ = 'turno_plantilla'
    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(50),  nullable=False)
    abreviacion     = db.Column(db.String(5),   nullable=False, unique=True)
    hora_inicio     = db.Column(db.Time(timezone=False), nullable=False)
    hora_fin        = db.Column(db.Time(timezone=False), nullable=False)
    color           = db.Column(db.String(10),  default='#18bc9c')
    dotacion_diaria = db.Column(db.Integer,     default=1)
    es_nocturno     = db.Column(db.Boolean,     default=False)
    activo          = db.Column(db.Boolean,     default=True)


class TipoAusenciaPlantilla(db.Model):
    """Plantillas globales de tipo de ausencia."""
    __tablename__ = 'tipo_ausencia_plantilla'
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(50),  nullable=False)
    abreviacion = db.Column(db.String(5),   nullable=False, unique=True)
    color       = db.Column(db.String(10),  default='#95a5a6')
    activo      = db.Column(db.Boolean,     default=True)
```

### 2.4 `business.py` — campo `es_base` en Turno y TipoAusencia

```python
# Agregar a clase Turno:
es_base = db.Column(db.Boolean, default=False, nullable=False)
# True = creado desde plantilla al crear empresa, no se puede eliminar

# Agregar a clase TipoAusencia:
es_base = db.Column(db.Boolean, default=False, nullable=False)

# Agregar a clase ReglaEmpresa:
es_base = db.Column(db.Boolean, default=False, nullable=False)
```

---

## 3. Migración de BD

Crear el archivo `migrations/versions/0002_multiempresa_auth.py`:

```python
"""
Migración: multiempresa_auth_roles
Agrega todo lo necesario para login, roles y multiempresa.

IMPORTANTE: Ajustar down_revision al ID de la última migración existente.
"""

from alembic import op
import sqlalchemy as sa

revision      = '0002_multiempresa_auth'
down_revision = None   # ← CAMBIAR: poner el ID de la última migración existente
branch_labels = None
depends_on    = None


def upgrade():
    # 1. Tabla usuario_empresa
    op.create_table(
        'usuario_empresa',
        sa.Column('id',         sa.Integer,  primary_key=True),
        sa.Column('usuario_id', sa.Integer,
                  sa.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False),
        sa.Column('empresa_id', sa.Integer,
                  sa.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activo',     sa.Boolean,  server_default='true', nullable=False),
        sa.Column('creado_en',  sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('usuario_id', 'empresa_id', name='uq_usuario_empresa'),
    )
    op.create_index('ix_ue_usuario', 'usuario_empresa', ['usuario_id'])
    op.create_index('ix_ue_empresa', 'usuario_empresa', ['empresa_id'])

    # 2. empresa_activa_id en usuario
    op.add_column('usuario',
        sa.Column('empresa_activa_id', sa.Integer,
                  sa.ForeignKey('empresa.id', ondelete='SET NULL'), nullable=True))

    # 3. endpoint, icono, orden en menu
    op.add_column('menu', sa.Column('endpoint', sa.String(100), nullable=True))
    op.add_column('menu', sa.Column('icono',    sa.String(50),  nullable=True))
    op.add_column('menu', sa.Column('orden',    sa.Integer,
                                    server_default='0', nullable=False))

    # 4. es_base en turno, tipo_ausencia, regla_empresa
    for tabla in ['turno', 'tipo_ausencia', 'regla_empresa']:
        op.add_column(tabla,
            sa.Column('es_base', sa.Boolean,
                      server_default='false', nullable=False))

    # 5. Tabla turno_plantilla
    op.create_table(
        'turno_plantilla',
        sa.Column('id',              sa.Integer, primary_key=True),
        sa.Column('nombre',          sa.String(50),  nullable=False),
        sa.Column('abreviacion',     sa.String(5),   nullable=False, unique=True),
        sa.Column('hora_inicio',     sa.Time(timezone=False), nullable=False),
        sa.Column('hora_fin',        sa.Time(timezone=False), nullable=False),
        sa.Column('color',           sa.String(10),  server_default='#18bc9c'),
        sa.Column('dotacion_diaria', sa.Integer,     server_default='1'),
        sa.Column('es_nocturno',     sa.Boolean,     server_default='false'),
        sa.Column('activo',          sa.Boolean,     server_default='true'),
        sa.Column('creado_en',       sa.DateTime,    server_default=sa.func.now()),
    )

    # 6. Tabla tipo_ausencia_plantilla
    op.create_table(
        'tipo_ausencia_plantilla',
        sa.Column('id',          sa.Integer,    primary_key=True),
        sa.Column('nombre',      sa.String(50), nullable=False),
        sa.Column('abreviacion', sa.String(5),  nullable=False, unique=True),
        sa.Column('color',       sa.String(10), server_default='#95a5a6'),
        sa.Column('activo',      sa.Boolean,    server_default='true'),
        sa.Column('creado_en',   sa.DateTime,   server_default=sa.func.now()),
    )

    # 7. Quitar unique de empresa.rut (permite varias sucursales con mismo RUT)
    try:
        op.drop_constraint('empresa_rut_key', 'empresa', type_='unique')
    except Exception:
        pass


def downgrade():
    op.create_unique_constraint('empresa_rut_key', 'empresa', ['rut'])
    op.drop_table('tipo_ausencia_plantilla')
    op.drop_table('turno_plantilla')
    for tabla in ['turno', 'tipo_ausencia', 'regla_empresa']:
        op.drop_column(tabla, 'es_base')
    op.drop_column('menu', 'orden')
    op.drop_column('menu', 'icono')
    op.drop_column('menu', 'endpoint')
    op.drop_column('usuario', 'empresa_activa_id')
    op.drop_index('ix_ue_empresa', 'usuario_empresa')
    op.drop_index('ix_ue_usuario', 'usuario_empresa')
    op.drop_table('usuario_empresa')
```

---

## 4. Archivos a modificar

### 4.1 `requirements.txt` — agregar flask-login

```
flask-login>=0.6     # autenticación
# Werkzeug ya viene con Flask (hashing de passwords)
```

### 4.2 `app/__init__.py` — inicializar Flask-Login y context_processor

```python
from flask import Flask, request as flask_request, session
from .config import Config
from .database import db
from flask_migrate import Migrate
from flask_login import LoginManager

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    # ── Flask-Login ───────────────────────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view             = 'main.login'
    login_manager.login_message          = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.auth import Usuario
        return Usuario.query.get(int(user_id))

    # ── Context processors ────────────────────────────────────────────────────
    @app.context_processor
    def inject_htmx():
        return {'is_htmx': flask_request.headers.get('HX-Request', False)}

    @app.context_processor
    def inject_nav_context():
        """
        Inyecta en TODOS los templates:
          nav_menus        → menús según el rol del usuario
          empresas_usuario → empresas que puede ver
          empresa_activa   → empresa seleccionada actualmente
        """
        from flask_login import current_user
        if not current_user.is_authenticated:
            return {
                'nav_menus':        [],
                'empresas_usuario': [],
                'empresa_activa':   None,
            }

        from app.models.auth import RolMenu, Menu
        from app.services.context import get_empresas_usuario, get_empresa_activa

        nav_menus = RolMenu.query\
            .filter_by(rol_id=current_user.rol_id)\
            .join(Menu)\
            .filter(Menu.activo == True)\
            .order_by(Menu.orden)\
            .all()

        return {
            'nav_menus':        nav_menus,
            'empresas_usuario': get_empresas_usuario(),
            'empresa_activa':   get_empresa_activa(),
        }

    # ── Auto-setup empresa (evento SQLAlchemy) ────────────────────────────────
    from app.services.empresa_setup import register_empresa_events
    register_empresa_events()

    # ── CLI commands ──────────────────────────────────────────────────────────
    _register_cli(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from .controllers.main_bp          import main_bp
    from .controllers.region_bp        import region_bp
    from .controllers.comuna_bp        import comuna_bp
    from .controllers.feriado_bp       import feriado_bp
    from .controllers.servicio_bp      import servicio_bp
    from .controllers.rol_bp           import rol_bp
    from .controllers.menu_bp          import menu_bp
    from .controllers.cliente_bp       import cliente_bp
    from .controllers.empresa_bp       import empresa_bp
    from .controllers.turno_bp         import turno_bp
    from .controllers.usuario_bp       import usuario_bp
    from .controllers.trabajador_bp    import trabajador_bp
    from .controllers.regla_bp         import regla_bp
    from .controllers.regla_empresa_bp import regla_empresa_bp
    from .controllers.planificacion_bp import planificacion_bp
    from .controllers.tipo_ausencia_bp import tipo_ausencia_bp
    from .controllers.parametro_legal_bp import parametro_legal_bp

    for bp in [main_bp, usuario_bp, region_bp, comuna_bp, empresa_bp,
               cliente_bp, servicio_bp, trabajador_bp, turno_bp,
               planificacion_bp, regla_bp, regla_empresa_bp, feriado_bp,
               tipo_ausencia_bp, menu_bp, rol_bp, parametro_legal_bp]:
        app.register_blueprint(bp)

    return app


def _register_cli(app):
    import click
    from flask.cli import with_appcontext

    @app.cli.command('seed-all')
    @click.option('--drop', is_flag=True, help='Recrear tablas (PELIGROSO)')
    @with_appcontext
    def seed_all(drop):
        """Pobla la BD con datos base en orden correcto."""
        if drop:
            click.confirm('⚠️ ¿Eliminar TODOS los datos?', abort=True)
            db.drop_all()
            db.create_all()
        import sys, os
        sys.path.insert(0, os.path.dirname(app.root_path))
        from seed_oficial import seed_all as _seed
        _seed()

    @app.cli.command('seed-feriados')
    @click.option('--anio', required=True, type=int)
    @with_appcontext
    def seed_feriados_cmd(anio):
        """Carga feriados desde API Boostr."""
        from seed_oficial import seed_feriados
        n = seed_feriados(anio)
        click.echo(f'✅ {n} feriados insertados para {anio}')
```

### 4.3 `app/controllers/main_bp.py` — login y logout reales

```python
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app.database import db
from app.models.auth import Usuario
from app.services.context import get_empresa_activa_id, get_empresas_usuario, usuario_tiene_acceso

main_bp = Blueprint('main', __name__)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        usuario  = Usuario.query.filter_by(email=email, activo=True).first()

        if usuario and usuario.check_password(password):
            login_user(usuario, remember=True)

            # Si tiene solo una empresa, seleccionarla automáticamente
            empresas = get_empresas_usuario()
            if len(empresas) == 1:
                session['empresa_activa_id'] = empresas[0].id

            return redirect(request.args.get('next') or url_for('main.index'))

        error = 'Email o contraseña incorrectos.'

    return render_template('login.html', error=error)


@main_bp.route('/logout')
@login_required
def logout():
    session.pop('empresa_activa_id', None)
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/')
@login_required
def index():
    from app.models.business import Empresa, Trabajador
    empresa_id = get_empresa_activa_id()

    if empresa_id:
        total_trabajadores = Trabajador.query.filter_by(
            empresa_id=empresa_id, activo=True).count()
        total_empresas = 1
    else:
        total_trabajadores = Trabajador.query.filter_by(activo=True).count()
        total_empresas     = Empresa.query.filter_by(activo=True).count()

    return render_template('index.html',
                           total_trabajadores=total_trabajadores,
                           total_empresas=total_empresas)


@main_bp.route('/cambiar-empresa/<int:empresa_id>', methods=['POST'])
@login_required
def cambiar_empresa(empresa_id):
    """Cambia la empresa activa en sesión. Verifica acceso."""
    if not usuario_tiene_acceso(current_user, empresa_id):
        return jsonify({'ok': False, 'msg': 'Sin acceso a esta empresa'}), 403

    from app.models.business import Empresa
    empresa = Empresa.query.get_or_404(empresa_id)

    session['empresa_activa_id']    = empresa_id
    current_user.empresa_activa_id  = empresa_id
    db.session.commit()

    return jsonify({'ok': True, 'empresa_nombre': empresa.razon_social})
```

---

## 5. Archivos nuevos a crear

### 5.1 `app/services/context.py`

```python
"""
Servicio central de contexto multiempresa.
Todas las queries filtradas por empresa pasan por aquí.
NO modifica ni importa nada del scheduler.
"""
from flask import session, abort
from flask_login import current_user


def get_empresa_activa_id():
    """
    Retorna empresa_id activo.
    Super Admin → session (puede ser None = ve todo)
    Cliente     → sus empresas via cliente_id
    Admin       → sus empresas via UsuarioEmpresa
    """
    if not current_user.is_authenticated:
        abort(401)

    if current_user.is_super_admin:
        return session.get('empresa_activa_id')

    empresa_id = session.get('empresa_activa_id')
    if not empresa_id:
        empresas = get_empresas_usuario()
        if empresas:
            empresa_id = empresas[0].id
            session['empresa_activa_id'] = empresa_id
        else:
            abort(403)

    if not usuario_tiene_acceso(current_user, empresa_id):
        abort(403)

    return empresa_id


def get_empresa_activa():
    """Retorna el objeto Empresa activa o None."""
    from app.models.business import Empresa
    empresa_id = get_empresa_activa_id()
    return Empresa.query.get(empresa_id) if empresa_id else None


def get_empresas_usuario():
    """Lista de empresas que puede ver el usuario actual."""
    from app.models.business import Empresa
    from app.models.auth import UsuarioEmpresa

    if current_user.is_super_admin:
        return Empresa.query.filter_by(activo=True)\
                            .order_by(Empresa.razon_social).all()

    if current_user.is_cliente:
        return Empresa.query.filter_by(
            cliente_id=current_user.cliente_id, activo=True
        ).order_by(Empresa.razon_social).all()

    # Administrador
    ids = [ue.empresa_id for ue in current_user.empresas if ue.activo]
    if not ids:
        return []
    return Empresa.query.filter(
        Empresa.id.in_(ids), Empresa.activo == True
    ).order_by(Empresa.razon_social).all()


def usuario_tiene_acceso(usuario, empresa_id):
    """Verifica si el usuario puede acceder a una empresa."""
    from app.models.business import Empresa
    from app.models.auth import UsuarioEmpresa

    if usuario.is_super_admin:
        return True

    if usuario.is_cliente:
        empresa = Empresa.query.get(empresa_id)
        return empresa and empresa.cliente_id == usuario.cliente_id

    return UsuarioEmpresa.query.filter_by(
        usuario_id=usuario.id,
        empresa_id=empresa_id,
        activo=True
    ).first() is not None
```

### 5.2 `app/services/empresa_setup.py`

```python
"""
Auto-setup al crear una empresa.
Usa evento SQLAlchemy — no requiere trigger de BD.
Al hacer INSERT en tabla empresa, crea automáticamente:
  - Turnos base (M, T, I, N) desde TurnoPlantilla
  - Tipos de ausencia base desde TipoAusenciaPlantilla
  - Reglas legales asignadas desde tabla Regla
"""
from sqlalchemy import event
from app.models.business import Empresa


def register_empresa_events():
    """Llamar desde create_app()."""
    event.listen(Empresa, 'after_insert', _on_empresa_created)


def _on_empresa_created(mapper, connection, empresa):
    from app.database import db
    from app.models.business import (
        Turno, TipoAusencia, ReglaEmpresa,
        TurnoPlantilla, TipoAusenciaPlantilla, Regla
    )

    # 1. Turnos base desde plantillas
    for p in TurnoPlantilla.query.filter_by(activo=True).all():
        db.session.add(Turno(
            empresa_id=empresa.id, nombre=p.nombre,
            abreviacion=p.abreviacion, hora_inicio=p.hora_inicio,
            hora_fin=p.hora_fin, color=p.color,
            dotacion_diaria=p.dotacion_diaria, es_nocturno=p.es_nocturno,
            es_base=True, activo=True,
        ))

    # 2. Tipos de ausencia base desde plantillas
    for p in TipoAusenciaPlantilla.query.filter_by(activo=True).all():
        db.session.add(TipoAusencia(
            empresa_id=empresa.id, nombre=p.nombre,
            abreviacion=p.abreviacion, color=p.color,
            es_base=True, activo=True,
        ))

    # 3. Reglas legales asignadas
    for r in Regla.query.filter_by(activo=True).all():
        db.session.add(ReglaEmpresa(
            empresa_id=empresa.id, regla_id=r.id,
            params_custom=None, es_base=True, activo=True,
        ))

    db.session.flush()
```

---

## 6. Layout y menú dinámico

### Selector de empresa y menú en `layout.html`

Reemplazar el menú hardcodeado y el nombre hardcodeado por:

```html
<!-- Selector de empresa activa -->
<div class="dropdown mb-2">
  <button class="btn btn-sm btn-outline-secondary w-100 dropdown-toggle text-start"
          type="button" data-bs-toggle="dropdown">
    <i class="fa fa-store me-1"></i>
    {{ empresa_activa.razon_social if empresa_activa else 'Seleccionar empresa' }}
  </button>
  <ul class="dropdown-menu w-100">
    {% for emp in empresas_usuario %}
    <li>
      <a class="dropdown-item {% if empresa_activa and emp.id == empresa_activa.id %}active{% endif %}"
         href="#"
         hx-post="/cambiar-empresa/{{ emp.id }}"
         hx-swap="none"
         hx-on::after-request="window.location.reload()">
        {{ emp.razon_social }}
      </a>
    </li>
    {% endfor %}
  </ul>
</div>

<!-- Menú dinámico según rol desde BD -->
<ul class="nav flex-column">
  {% for item in nav_menus %}
  <li class="nav-item">
    <a class="nav-link {% if request.endpoint == item.menu_asociado.endpoint %}active{% endif %}"
       href="{{ url_for(item.menu_asociado.endpoint) }}">
      <i class="fa {{ item.menu_asociado.icono }} me-2"></i>
      {{ item.menu_asociado.nombre }}
    </a>
  </li>
  {% endfor %}
</ul>

<!-- Usuario logueado (reemplazar texto hardcodeado) -->
<div class="mt-auto p-2 border-top">
  <p class="mb-0 fw-bold small">{{ current_user.nombre }} {{ current_user.apellidos }}</p>
  <small class="text-muted">{{ current_user.rol.descripcion }}</small>
  <a href="{{ url_for('main.logout') }}" class="btn btn-sm btn-outline-danger w-100 mt-1">
    <i class="fa fa-right-from-bracket me-1"></i> Cerrar sesión
  </a>
</div>
```

---

## 7. Seed de roles, menús y Super Admin

Estos datos van en `seed_oficial.py` (ver archivo separado).
Aquí solo el resumen de qué roles ven qué menús:

### Menús por rol

| Menú | Super Admin | Cliente | Administrador |
|---|---|---|---|
| Dashboard | ✅ | ✅ | ✅ |
| Planificación | ✅ | ✅ | ✅ |
| Trabajadores | ✅ | ✅ | ✅ |
| Turnos | ✅ | ✅ | ✅ |
| Ausencias | ✅ | ✅ | ✅ |
| Tipos de Ausencia | ✅ | ✅ | ✅ |
| Reglas Empresa | ✅ | ✅ | ✅ |
| Clientes | ✅ | ❌ | ❌ |
| Empresas | ✅ | ❌ | ❌ |
| Usuarios | ✅ | ❌ | ❌ |
| Servicios | ✅ | ❌ | ❌ |
| Feriados | ✅ | ❌ | ❌ |
| Reglas Generales | ✅ | ❌ | ❌ |
| Parámetros Legales | ✅ | ❌ | ❌ |
| Regiones / Comunas | ✅ | ❌ | ❌ |
| Roles / Menús | ✅ | ❌ | ❌ |

### Credenciales iniciales

```
Email:    admin@sgt.cl
Password: Admin2026!
Rol:      Super Admin
```
**⚠️ Cambiar la contraseña después del primer login.**

---

## 8. Patrón estándar para blueprints

Aplicar a todos los blueprints existentes. Son exactamente 2 cambios por handler:

```python
# ANTES:
from flask import Blueprint, render_template
bp = Blueprint('trabajador', __name__, url_prefix='/trabajadores')

@bp.route('/')
def index():
    registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('trabajadores.html', registros=registros)


# DESPUÉS:
from flask import Blueprint, render_template
from flask_login import login_required                          # ← agregar
from app.services.context import get_empresa_activa_id         # ← agregar
bp = Blueprint('trabajador', __name__, url_prefix='/trabajadores')

@bp.route('/')
@login_required                                                 # ← agregar
def index():
    empresa_id = get_empresa_activa_id()                        # ← agregar
    if empresa_id:
        registros = Trabajador.query\
            .filter_by(empresa_id=empresa_id)\
            .order_by(Trabajador.nombre).all()
    else:
        # Super Admin sin empresa activa → ve todo
        registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('trabajadores.html', registros=registros)
```

### Blueprints que necesitan el patrón

| Blueprint | Filtro por | Notas |
|---|---|---|
| `trabajador_bp` | `empresa_id` | |
| `turno_bp` | `empresa_id` | |
| `tipo_ausencia_bp` | `empresa_id` | |
| `planificacion_bp` | `empresa_id` via primer trabajador | ya lo hace internamente |
| `regla_empresa_bp` | `empresa_id` | |
| `empresa_bp` | `cliente_id` | Cliente solo ve sus empresas |
| `usuario_bp` | `cliente_id` | Admin solo crea usuarios de su cliente |
| `servicio_bp` | `activo=True` | los servicios son globales |
| `region_bp` | sin filtro | datos globales |
| `comuna_bp` | sin filtro | datos globales |
| `feriado_bp` | sin filtro | datos globales |
| `regla_bp` | sin filtro | datos globales |
| `parametro_legal_bp` | sin filtro | datos globales, solo Super Admin |

### Protección `es_base` en eliminaciones

```python
# En turno_bp, tipo_ausencia_bp, regla_empresa_bp:
@bp.route('/eliminar', methods=['POST'])
@login_required
def eliminar():
    registro = Turno.query.get_or_404(int(request.form.get('id')))
    if registro.es_base:
        return jsonify({
            'ok':  False,
            'msg': 'Este registro es base del sistema y no puede eliminarse. '
                   'Puede desactivarlo si no lo necesita.'
        }), 400
    db.session.delete(registro)
    db.session.commit()
    return jsonify({'ok': True})
```

---

## 9. Plan de implementación paso a paso

### Sprint A — Login (2-3 días)

```
Día 1:
  1. pip install flask-login
  2. Actualizar auth.py con UserMixin + métodos de password
  3. Actualizar __init__.py con LoginManager
  4. Actualizar main_bp.py con login/logout reales
  5. Correr: flask db upgrade (migración 0002)
  6. Correr: python seed_oficial.py
  7. Verificar login con admin@sgt.cl / Admin2026!

Día 2:
  8. Agregar @login_required a todos los blueprints
  9. Probar que sin login redirige a /login
  10. Probar que con login accede normalmente
```

### Sprint B — Multiempresa (2-3 días)

```
Día 3:
  1. Crear app/services/context.py
  2. Actualizar __init__.py con context_processor
  3. Crear empresa_setup.py con evento after_insert
  4. Actualizar trabajador_bp.py con filtro empresa_id
  5. Probar: crear empresa → se crean turnos y ausencias automáticamente

Día 4:
  6. Actualizar turno_bp, tipo_ausencia_bp, regla_empresa_bp
  7. Actualizar empresa_bp con filtro cliente_id
  8. Crear usuario de prueba tipo Cliente y verificar que solo ve sus empresas
```

### Sprint C — Menú dinámico (1 día)

```
Día 5:
  1. Actualizar layout.html con menú dinámico desde nav_menus
  2. Agregar selector de empresa al menú
  3. Mostrar nombre real del usuario (no hardcodeado)
  4. Probar que cada rol ve solo sus menús
  5. Probar cambio de empresa activa
```

### Verificación final

```
✅ Sin login → redirige a /login
✅ Login con credenciales incorrectas → mensaje de error
✅ Login correcto → dashboard
✅ Super Admin ve todos los menús y todas las empresas
✅ Cliente ve solo sus menús y sus empresas
✅ Admin ve solo sus menús y sus empresas asignadas
✅ Cambiar empresa activa → queries cambian de contexto
✅ Crear empresa → turnos M,T,I,N se crean automáticamente
✅ No se puede eliminar turno con es_base=True
✅ Logout → redirige a /login, sesión limpiada
```

---

## 10. Preparación para Redis

El sistema actual usa sesiones de Flask en cookies firmadas.
Para pasar a Redis en producción solo hay que cambiar 3 líneas:

### Paso 1 — Descomentar en `requirements.txt`

```
flask-session>=0.8
redis>=5.0
```

### Paso 2 — Agregar a `config.py`

```python
# Sesiones en Redis (producción)
SESSION_TYPE             = 'redis'
SESSION_REDIS            = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
SESSION_PERMANENT        = True
SESSION_USE_SIGNER       = True   # firma la cookie para seguridad
PERMANENT_SESSION_LIFETIME = 86400 * 7   # 7 días
```

### Paso 3 — En `__init__.py`

```python
from flask_session import Session

def create_app():
    ...
    Session(app)   # ← agregar después de db.init_app(app)
    ...
```

### Por qué Redis es importante en producción

```
Sin Redis (hoy — sesiones en cookies):
  ✅ Simple, funciona sin infraestructura extra
  ❌ Si el servidor reinicia → todos pierden la sesión
  ❌ Si escalas a 2+ instancias → sesiones no se comparten

Con Redis:
  ✅ Sesiones persisten aunque el contenedor reinicie
  ✅ Múltiples instancias comparten las sesiones
  ✅ El contexto empresa_activa_id persiste correctamente
```

Todo el código de contexto (`session['empresa_activa_id']`) funciona
igual con ambos backends — el cambio es transparente al código existente.

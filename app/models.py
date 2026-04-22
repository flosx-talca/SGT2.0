from database import db
from datetime import datetime

# ==========================================
# 1. REGION Y COMUNA
# ==========================================
class Region(db.Model):
    __tablename__ = 'region'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False, unique=True)
    descripcion = db.Column(db.String(150), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comunas = db.relationship('Comuna', backref='region', lazy=True)
    feriados = db.relationship('Feriado', backref='region_asociada', lazy=True)

class Comuna(db.Model):
    __tablename__ = 'comuna'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    descripcion = db.Column(db.String(150), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id', ondelete='RESTRICT'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresas = db.relationship('Empresa', backref='comuna', lazy=True)

# ==========================================
# 2. ROL, MENU Y PERMISOS
# ==========================================
class Rol(db.Model):
    __tablename__ = 'rol'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuarios = db.relationship('Usuario', backref='rol', lazy=True)
    menus = db.relationship('RolMenu', backref='rol_asociado', lazy=True, cascade="all, delete-orphan")

class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = db.relationship('RolMenu', backref='menu_asociado', lazy=True, cascade="all, delete-orphan")

class RolMenu(db.Model):
    __tablename__ = 'rol_menu'
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id', ondelete='CASCADE'), primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'), primary_key=True)
    puede_crear = db.Column(db.Boolean, default=False)
    puede_editar = db.Column(db.Boolean, default=False)
    puede_eliminar = db.Column(db.Boolean, default=False)

# ==========================================
# 3. CLIENTE Y EMPRESA
# ==========================================
class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(15), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresas = db.relationship('Empresa', backref='dueño', lazy=True)
    usuarios = db.relationship('Usuario', backref='cliente', lazy=True)

# Relación Muchos a Muchos: Empresa <-> Servicio
empresa_servicio = db.Table('empresa_servicio',
    db.Column('empresa_id', db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), primary_key=True),
    db.Column('servicio_id', db.Integer, db.ForeignKey('servicio.id', ondelete='CASCADE'), primary_key=True)
)

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(15), nullable=False, unique=True)
    razon_social = db.Column(db.String(200), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id', ondelete='RESTRICT'), nullable=False)
    comuna_id = db.Column(db.Integer, db.ForeignKey('comuna.id', ondelete='RESTRICT'), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turnos = db.relationship('Turno', backref='empresa', lazy=True, cascade="all, delete-orphan")
    trabajadores = db.relationship('Trabajador', backref='empresa', lazy=True)
    servicios = db.relationship('Servicio', secondary=empresa_servicio, backref=db.backref('empresas_asociadas', lazy='dynamic'))

# ==========================================
# 4. USUARIO
# ==========================================
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(15), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id', ondelete='RESTRICT'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id', ondelete='CASCADE'), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==========================================
# 5. FERIADO
# ==========================================
class Feriado(db.Model):
    __tablename__ = 'feriado'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    es_regional = db.Column(db.Boolean, default=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id', ondelete='CASCADE'), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==========================================
# 6. SERVICIO Y TURNO
# ==========================================
class Servicio(db.Model):
    __tablename__ = 'servicio'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trabajadores = db.relationship('Trabajador', backref='servicio', lazy=True)

class Turno(db.Model):
    __tablename__ = 'turno'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    abreviacion = db.Column(db.String(5), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    color = db.Column(db.String(10), default='#18bc9c')
    dotacion_diaria = db.Column(db.Integer, default=1)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==========================================
# 7. TRABAJADOR
# ==========================================
class Trabajador(db.Model):
    __tablename__ = 'trabajador'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(15), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido1 = db.Column(db.String(100), nullable=False)
    apellido2 = db.Column(db.String(100))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='RESTRICT'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id', ondelete='RESTRICT'), nullable=False)
    cargo = db.Column(db.String(100))
    email = db.Column(db.String(150))
    telefono = db.Column(db.String(20))
    tipo_contrato = db.Column(db.String(50), nullable=False, default='full-time')
    horas_semanales = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    preferencias = db.relationship('TrabajadorPreferencia', backref='trabajador', lazy=True, cascade="all, delete-orphan")
    ausencias = db.relationship('TrabajadorAusencia', backref='trabajador', lazy=True, cascade="all, delete-orphan")

class TrabajadorPreferencia(db.Model):
    __tablename__ = 'trabajador_preferencia'
    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)
    turno = db.Column(db.String(5), nullable=False)

class TrabajadorAusencia(db.Model):
    __tablename__ = 'trabajador_ausencia'
    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(20), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

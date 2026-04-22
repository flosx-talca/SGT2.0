from app.database import db
from datetime import datetime

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


# ─── Motor de Reglas ──────────────────────────────────────────────────────────

class ReglaFamilia(db.Model):
    __tablename__ = 'regla_familia'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)

    reglas = db.relationship('ReglaCatalogo', backref='familia', lazy=True)


class ReglaCatalogo(db.Model):
    __tablename__ = 'regla_catalogo'
    id = db.Column(db.Integer, primary_key=True)
    familia_id = db.Column(db.Integer, db.ForeignKey('regla_familia.id', ondelete='RESTRICT'), nullable=False)
    codigo = db.Column(db.String(100), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    rule_type = db.Column(db.String(20), nullable=False)        # hard | soft | client_rule | worker_restriction
    scope = db.Column(db.String(20), nullable=False)            # empresa | sucursal | area | trabajador
    field = db.Column(db.String(100))
    operator = db.Column(db.String(10))
    params_default = db.Column(db.JSON)
    params_editables = db.Column(db.JSON)                       # lista de keys que el cliente puede editar
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    asignaciones = db.relationship('ReglaEmpresa', backref='catalogo', lazy=True, cascade='all, delete-orphan')


class ReglaEmpresa(db.Model):
    __tablename__ = 'regla_empresa'
    id = db.Column(db.Integer, primary_key=True)
    regla_catalogo_id = db.Column(db.Integer, db.ForeignKey('regla_catalogo.id', ondelete='CASCADE'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    params = db.Column(db.JSON)
    is_enabled = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = db.relationship('Empresa', backref=db.backref('reglas_empresa', lazy=True))

    __table_args__ = (db.UniqueConstraint('regla_catalogo_id', 'empresa_id', name='uq_regla_empresa'),)

from app.database import db
from datetime import datetime
from app.models.enums import TipoContrato, CategoriaAusencia

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
    rut = db.Column(db.String(15), nullable=False) # Removido unique para sucursales
    razon_social = db.Column(db.String(200), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id', ondelete='RESTRICT'), nullable=False)
    comuna_id = db.Column(db.Integer, db.ForeignKey('comuna.id', ondelete='RESTRICT'), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turnos = db.relationship('Turno', backref='empresa', lazy=True, cascade="all, delete-orphan")
    trabajadores = db.relationship('Trabajador', backref='empresa', lazy=True)
    servicios = db.relationship('Servicio', secondary=empresa_servicio,
                                backref=db.backref('empresas_asociadas', lazy='dynamic'))
    reglas = db.relationship('ReglaEmpresa', backref='empresa', lazy=True, cascade="all, delete-orphan")


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
    # db.Time(timezone=False) → PostgreSQL TIME WITHOUT TIME ZONE
    # En Python se manipula como datetime.time: usa .hour y .minute
    # Ejemplo: hora_inicio.hour * 60 + hora_inicio.minute = minutos desde medianoche
    hora_inicio = db.Column(db.Time(timezone=False), nullable=False)
    hora_fin    = db.Column(db.Time(timezone=False), nullable=False)
    color = db.Column(db.String(10), default='#18bc9c')
    dotacion_diaria = db.Column(db.Integer, default=1)
    # es_nocturno: True si el turno cruza medianoche (hora_fin <= hora_inicio).
    # Se calcula automáticamente al guardar en turno_bp.py, no requiere input del usuario.
    # Migración: ver a1b2c3d4e5f6_add_es_nocturno_nuevas_reglas.py
    es_nocturno = db.Column(db.Boolean, default=False, nullable=False)
    es_base = db.Column(db.Boolean, default=False, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def duracion_hrs(self) -> float:
        """Calcula la duración en horas del turno."""
        if not self.hora_inicio or not self.hora_fin:
            return 8.0
        h_ini = self.hora_inicio.hour * 60 + self.hora_inicio.minute
        h_fin = self.hora_fin.hour   * 60 + self.hora_fin.minute
        if h_fin <= h_ini:
            h_fin += 24 * 60
        return round((h_fin - h_ini) / 60, 2)


class TipoAusencia(db.Model):
    __tablename__ = 'tipo_ausencia'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    abreviacion = db.Column(db.String(5), nullable=False)
    color = db.Column(db.String(10), default='#95a5a6')
    
    # ── CAMPOS NUEVOS SGT 2.1 ─────────────────────────────────────────────
    categoria = db.Column(
        db.Enum(CategoriaAusencia), 
        nullable=False, 
        default=CategoriaAusencia.AUSENCIA
    )
    tipo_restriccion = db.Column(db.String(30), nullable=True)
    es_base = db.Column(db.Boolean, default=False, nullable=False)
    # ──────────────────────────────────────────────────────────────────────
    
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa = db.relationship('Empresa', backref=db.backref('tipos_ausencia', lazy=True))


class ParametroLegal(db.Model):
    __tablename__ = "parametro_legal"

    id             = db.Column(db.Integer, primary_key=True)
    codigo         = db.Column(db.String(60), nullable=False, unique=True)
    valor          = db.Column(db.Float, nullable=False)
    categoria      = db.Column(db.String(50), nullable=False, default="General")
    descripcion    = db.Column(db.String(255), nullable=True)
    es_activo      = db.Column(db.Boolean, default=True, nullable=False)
    es_obligatorio = db.Column(db.Boolean, default=True, nullable=False)
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
    tipo_contrato = db.Column(db.Enum(TipoContrato), nullable=False, default=TipoContrato.FULL_TIME)
    # horas_semanales: horas contractuales por semana.
    # El builder usa este valor para calcular la meta mensual de turnos.
    # Ejemplos: 42 (jornada estándar Chile), 32 (part-time), 24 (part-time menor).
    # NOT NULL con default 42. Migración: ver b2c3d4e5f6a7_trabajador_horas_turno_hora.py
    horas_semanales = db.Column(db.Integer, nullable=False, default=42)
    permite_horas_extra = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    preferencias = db.relationship('TrabajadorPreferencia', backref='trabajador',
                                   lazy=True, cascade="all, delete-orphan")
    ausencias = db.relationship('TrabajadorAusencia', backref='trabajador',
                                lazy=True, cascade="all, delete-orphan")


class TrabajadorPreferencia(db.Model):
    __tablename__ = 'trabajador_preferencia'
    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)
    turno = db.Column(db.String(5), nullable=False)
    # tipo: 'preferencia', 'fijo', 'solo_turno'
    tipo = db.Column(db.String(20), nullable=False, default='preferencia')


class TrabajadorAusencia(db.Model):
    __tablename__ = 'trabajador_ausencia'
    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(255), nullable=False, default='')
    tipo_ausencia_id = db.Column(db.Integer, db.ForeignKey('tipo_ausencia.id', ondelete='CASCADE'), nullable=True)
    tipo_ausencia = db.relationship('TipoAusencia', lazy=True)
    
    # Vincular con la tabla técnica si es una RESTRICCION
    restriccion_id = db.Column(db.Integer, db.ForeignKey('trabajador_restriccion_turno.id'), nullable=True)
    restriccion = db.relationship('TrabajadorRestriccionTurno', foreign_keys=[restriccion_id])

    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

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
    def tipo_restriccion_val(self) -> str | None:
        """Retorna el tipo de restricción si aplica."""
        if self.tipo_ausencia is None:
            return None
        return self.tipo_ausencia.tipo_restriccion


class TrabajadorRestriccionTurno(db.Model):
    __tablename__ = "trabajador_restriccion_turno"

    id            = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajador.id", ondelete="CASCADE"), nullable=False)
    empresa_id    = db.Column(db.Integer, db.ForeignKey("empresa.id",    ondelete="CASCADE"), nullable=False)

    tipo = db.Column(db.String(30), nullable=False)
    naturaleza = db.Column(db.String(10), nullable=False) # 'hard' o 'soft'

    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin    = db.Column(db.Date, nullable=False)

    dias_semana  = db.Column(db.JSON, nullable=True) # [0=lun, 1=mar, ..., 6=dom]

    turno_id             = db.Column(db.Integer, db.ForeignKey("turno.id", ondelete="RESTRICT"), nullable=True)
    turno_alternativo_id = db.Column(db.Integer, db.ForeignKey("turno.id", ondelete="RESTRICT"), nullable=True)

    motivo    = db.Column(db.String(200), nullable=True)
    activo    = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    trabajador = db.relationship("Trabajador", backref=db.backref("restricciones_turno", lazy=True))
    turno      = db.relationship("Turno", foreign_keys=[turno_id], lazy=True)
    turno_alt  = db.relationship("Turno", foreign_keys=[turno_alternativo_id], lazy=True)


class Regla(db.Model):
    __tablename__ = 'regla'
    __table_args__ = (
        db.Index('ix_regla_activo', 'activo'),
    )
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    familia = db.Column(db.String(50), nullable=False)
    tipo_regla = db.Column(db.String(20), nullable=False)
    scope = db.Column(db.String(50), nullable=False)
    campo = db.Column(db.String(100))
    operador = db.Column(db.String(20))
    params_base = db.Column(db.JSON)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asignaciones = db.relationship('ReglaEmpresa', backref='regla_rel',
                                   lazy=True, cascade="all, delete-orphan")


class ReglaEmpresa(db.Model):
    __tablename__ = 'regla_empresa'
    __table_args__ = (
        db.Index('ix_regla_empresa_activo', 'activo'),
        db.Index('ix_regla_empresa_empresa_id', 'empresa_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    regla_id = db.Column(db.Integer, db.ForeignKey('regla.id', ondelete='CASCADE'), nullable=False)
    params_custom = db.Column(db.JSON)
    es_base = db.Column(db.Boolean, default=False, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TurnoPlantilla(db.Model):
    __tablename__ = 'turno_plantilla'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    abreviacion = db.Column(db.String(5), nullable=False, unique=True)
    hora_inicio = db.Column(db.Time(timezone=False), nullable=False)
    hora_fin    = db.Column(db.Time(timezone=False), nullable=False)
    color = db.Column(db.String(10), default='#18bc9c')
    dotacion_diaria = db.Column(db.Integer, default=1)
    es_nocturno = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

class TipoAusenciaPlantilla(db.Model):
    __tablename__ = 'tipo_ausencia_plantilla'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    abreviacion = db.Column(db.String(5), nullable=False, unique=True)
    color = db.Column(db.String(10), default='#95a5a6')
    categoria = db.Column(db.Enum(CategoriaAusencia), nullable=False, default=CategoriaAusencia.AUSENCIA)
    tipo_restriccion = db.Column(db.String(30), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

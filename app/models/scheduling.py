from datetime import datetime
from app import db

class CuadranteCabecera(db.Model):
    __tablename__ = 'cuadrante_cabecera'

    id                   = db.Column(db.Integer, primary_key=True)
    empresa_id           = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    servicio_id          = db.Column(db.Integer, db.ForeignKey('servicio.id', ondelete='SET NULL'), nullable=True)
    mes                  = db.Column(db.SmallInteger, nullable=False)
    anio                 = db.Column(db.SmallInteger, nullable=False)
    estado               = db.Column(db.String(20), default='guardado')
    generado_por_user_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
    generado_en          = db.Column(db.DateTime, default=datetime.utcnow)
    guardado_por_user_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
    guardado_en          = db.Column(db.DateTime)
    creado_en            = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    asignaciones = db.relationship('CuadranteAsignacion', backref='cabecera',
                                   lazy='dynamic', cascade='all, delete-orphan')
    empresa      = db.relationship('Empresa', foreign_keys=[empresa_id])
    servicio     = db.relationship('Servicio', foreign_keys=[servicio_id])
    generado_por = db.relationship('Usuario', foreign_keys=[generado_por_user_id])
    guardado_por = db.relationship('Usuario', foreign_keys=[guardado_por_user_id])

    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'servicio_id', 'mes', 'anio', name='uq_cuadrante_periodo'),
        db.Index('idx_cab_empresa', 'empresa_id', 'anio', 'mes'),
    )

    @property
    def periodo(self):
        meses = ['Ene','Feb','Mar','Abr','May','Jun',
                 'Jul','Ago','Sep','Oct','Nov','Dic']
        return f"{meses[self.mes - 1]} {self.anio}"

    @property
    def total_asignaciones(self):
        from sqlalchemy import select, func
        from app import db as _db
        return _db.session.execute(
            select(func.count()).select_from(CuadranteAsignacion)
            .where(CuadranteAsignacion.cabecera_id == self.id)
        ).scalar()

    @property
    def total_manuales(self):
        from sqlalchemy import select, func
        from app import db as _db
        return _db.session.execute(
            select(func.count()).select_from(CuadranteAsignacion)
            .where(CuadranteAsignacion.cabecera_id == self.id,
                   CuadranteAsignacion.origen == 'manual')
        ).scalar()


class CuadranteAsignacion(db.Model):
    __tablename__ = 'cuadrante_asignacion'

    id                     = db.Column(db.Integer, primary_key=True)
    cabecera_id            = db.Column(db.Integer, db.ForeignKey('cuadrante_cabecera.id', ondelete='CASCADE'), nullable=False)
    trabajador_id          = db.Column(db.Integer, db.ForeignKey('trabajador.id', ondelete='CASCADE'), nullable=False)
    fecha                  = db.Column(db.Date, nullable=False)
    turno_id               = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    es_libre               = db.Column(db.Boolean, default=False)
    horas_asignadas        = db.Column(db.Numeric(4, 2), default=0)
    origen                 = db.Column(db.String(10), default='solver')
    modificado_por_user_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
    modificado_en          = db.Column(db.DateTime)
    
    # Flags de clasificación legal
    es_feriado             = db.Column(db.Boolean, default=False)
    es_domingo             = db.Column(db.Boolean, default=False)
    es_irrenunciable       = db.Column(db.Boolean, default=False)
    es_feriado_regional    = db.Column(db.Boolean, default=False)
    tipo_dia               = db.Column(db.String(30), default='normal')

    # Relaciones
    turno        = db.relationship('Turno', foreign_keys=[turno_id])
    trabajador   = db.relationship('Trabajador', foreign_keys=[trabajador_id])
    modificado_por = db.relationship('Usuario', foreign_keys=[modificado_por_user_id])

    __table_args__ = (
        db.UniqueConstraint('cabecera_id', 'trabajador_id', 'fecha', name='uq_asignacion_trabajador_fecha'),
        db.Index('idx_asig_cabecera', 'cabecera_id'),
        db.Index('idx_asig_trabajador', 'trabajador_id', 'fecha'),
        db.Index('idx_asig_origen', 'origen'),
    )

    @property
    def es_manual(self):
        return self.origen == 'manual'


class CuadranteAuditoria(db.Model):
    __tablename__ = 'cuadrante_auditoria'

    id                = db.Column(db.Integer, primary_key=True)
    asignacion_id     = db.Column(db.Integer, db.ForeignKey('cuadrante_asignacion.id', ondelete='CASCADE'), nullable=False)
    cabecera_id       = db.Column(db.Integer, db.ForeignKey('cuadrante_cabecera.id', ondelete='CASCADE'), nullable=False)
    user_id           = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    fecha_cambio      = db.Column(db.DateTime, default=datetime.utcnow)
    turno_anterior_id = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    turno_nuevo_id    = db.Column(db.Integer, db.ForeignKey('turno.id', ondelete='SET NULL'), nullable=True)
    era_libre_antes   = db.Column(db.Boolean, default=False)
    es_libre_ahora    = db.Column(db.Boolean, default=False)
    ip_address        = db.Column(db.String(45))
    motivo            = db.Column(db.String(255))

    # Relaciones
    usuario           = db.relationship('Usuario', foreign_keys=[user_id])
    turno_anterior    = db.relationship('Turno', foreign_keys=[turno_anterior_id])
    turno_nuevo       = db.relationship('Turno', foreign_keys=[turno_nuevo_id])

    __table_args__ = (
        db.Index('idx_aud_asignacion', 'asignacion_id'),
        db.Index('idx_aud_user', 'user_id', 'fecha_cambio'),
        db.Index('idx_aud_cabecera', 'cabecera_id', 'fecha_cambio'),
    )

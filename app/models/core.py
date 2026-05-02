from app.database import db
from datetime import datetime

class Region(db.Model):
    __tablename__ = 'region'
    __table_args__ = (
        db.Index('ix_region_activo', 'activo'),
        db.Index('ix_region_codigo', 'codigo'),
    )
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
    __table_args__ = (
        db.Index('ix_comuna_activo', 'activo'),
        db.Index('ix_comuna_region_id', 'region_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    descripcion = db.Column(db.String(150), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id', ondelete='RESTRICT'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresas = db.relationship('Empresa', backref='comuna', lazy=True)

class Feriado(db.Model):
    __tablename__ = 'feriado'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    es_irrenunciable = db.Column(db.Boolean, default=False)
    es_regional = db.Column(db.Boolean, default=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id', ondelete='CASCADE'), nullable=True)
    tipo = db.Column(db.String(20), default='nacional')
    regiones = db.Column(db.String(100), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fuente = db.Column(db.String(50), default='feriados.io')
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

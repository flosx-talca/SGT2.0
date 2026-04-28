from app.database import db
from datetime import datetime
from flask_login import UserMixin

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

    # Campos nuevos SGT 2.1
    endpoint = db.Column(db.String(100), nullable=True)
    icono = db.Column(db.String(50), nullable=True)
    orden = db.Column(db.Integer, default=0, nullable=False)
    es_base = db.Column(db.Boolean, default=False, nullable=False)

class RolMenu(db.Model):
    __tablename__ = 'rol_menu'
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id', ondelete='CASCADE'), primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'), primary_key=True)
    puede_crear = db.Column(db.Boolean, default=False)
    puede_editar = db.Column(db.Boolean, default=False)
    puede_eliminar = db.Column(db.Boolean, default=False)

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(15), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id', ondelete='RESTRICT'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id', ondelete='CASCADE'), nullable=True)
    
    # Campo nuevo SGT 2.1
    empresa_activa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='SET NULL'), nullable=True)
    
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    empresas = db.relationship('UsuarioEmpresa', backref='usuario', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.id)

class UsuarioEmpresa(db.Model):
    __tablename__ = 'usuario_empresa'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    empresa = db.relationship('Empresa', backref=db.backref('usuarios_asignados', lazy=True))

"""
seed.py - Script simplificado para poblar la base de datos SGT.
Ejecutar desde la raíz del proyecto: python -m app.seed
"""
import sys
import os
from datetime import date, time
import hashlib

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.core import Region, Comuna, Feriado
from app.models.auth import Rol, Menu, Usuario
from app.models.business import Cliente, Empresa, Servicio, Turno, Trabajador

app = create_app()

def seed():
    with app.app_context():
        print("🗑️  Limpiando base de datos...")
        db.drop_all()
        db.create_all()
        print("✅ Tablas creadas.\n")

        # ─── REGIONES Y COMUNAS ──────────────────────────────────────────────
        print("🌎 Insertando Regiones y Comunas...")
        rm = Region(codigo="RM", descripcion="Región Metropolitana")
        db.session.add(rm)
        db.session.commit()
        
        c_stgo = Comuna(codigo="STGO", descripcion="Santiago", region_id=rm.id)
        db.session.add(c_stgo)
        db.session.commit()

        # ─── FERIADOS ────────────────────────────────────────────────────────
        print("📅 Insertando Feriados...")
        f1 = Feriado(fecha=date(2025, 1, 1), descripcion="Año Nuevo")
        db.session.add(f1)
        db.session.commit()

        # ─── ROLES Y MENÚS ───────────────────────────────────────────────────
        print("🎭 Insertando Roles y Menús...")
        rol_super = Rol(descripcion="Super Admin")
        db.session.add(rol_super)
        db.session.commit()

        menus_data = ["Dashboard", "Trabajadores", "Turnos", "Planificación", "Clientes", "Usuarios", "Empresas"]
        for m_name in menus_data:
            db.session.add(Menu(nombre=m_name))
        db.session.commit()

        # ─── CLIENTE Y EMPRESA ───────────────────────────────────────────────
        print("🏢 Insertando Cliente y Empresa Principal...")
        c1 = Cliente(rut="11111111-1", nombre="Admin", apellidos="SGT", email="contacto@sgt.cl")
        db.session.add(c1)
        db.session.commit()

        e1 = Empresa(rut="76111111-1", razon_social="Empresa Demo SGT", cliente_id=c1.id, comuna_id=c_stgo.id, direccion="Av. Principal 123")
        db.session.add(e1)
        db.session.commit()

        # ─── SERVICIOS ───────────────────────────────────────────────────────
        print("⚙️  Insertando Servicios...")
        s_pista = Servicio(descripcion="Pista Combustible")
        s_pronto = Servicio(descripcion="Tienda Pronto")
        db.session.add_all([s_pista, s_pronto])
        db.session.commit()
        e1.servicios = [s_pista, s_pronto]
        db.session.commit()

        # ─── TURNOS (SOLO 4) ─────────────────────────────────────────────────
        print("🕐 Insertando Turnos (MAÑANA, TARDE, INTERMEDIO, NOCHE)...")
        turnos = [
            Turno(empresa_id=e1.id, nombre="MAÑANA",     abreviacion="M", hora_inicio=time(7,0),  hora_fin=time(15,0), color="#3498db", dotacion_diaria=3),
            Turno(empresa_id=e1.id, nombre="TARDE",      abreviacion="T", hora_inicio=time(15,0), hora_fin=time(23,0), color="#e67e22", dotacion_diaria=3),
            Turno(empresa_id=e1.id, nombre="NOCHE",      abreviacion="N", hora_inicio=time(23,0), hora_fin=time(7,0),  color="#2c3e50", dotacion_diaria=2),
            Turno(empresa_id=e1.id, nombre="INTERMEDIO", abreviacion="I", hora_inicio=time(11,0), hora_fin=time(19,0), color="#1abc9c", dotacion_diaria=2),
        ]
        db.session.add_all(turnos)
        db.session.commit()

        # ─── TRABAJADORES ────────────────────────────────────────────────────
        print("👷 Insertando Trabajadores...")
        trabajadores = [
            dict(rut="10100001-1", nombre="Carlos",   apellido1="Muñoz",    empresa_id=e1.id, servicio_id=s_pista.id, cargo="Operario", email="carlos@sgt.cl"),
            dict(rut="10100002-2", nombre="Ana",      apellido1="Torres",   empresa_id=e1.id, servicio_id=s_pista.id, cargo="Operario", email="ana@sgt.cl"),
            dict(rut="10100003-3", nombre="Diego",    apellido1="Salinas",  empresa_id=e1.id, servicio_id=s_pronto.id, cargo="Cajero", email="diego@sgt.cl"),
            dict(rut="10100004-4", nombre="Valentina",apellido1="Reyes",    empresa_id=e1.id, servicio_id=s_pronto.id, cargo="Cajero", email="valentina@sgt.cl"),
            dict(rut="10100005-5", nombre="Felipe",   apellido1="Contreras",empresa_id=e1.id, servicio_id=s_pista.id, cargo="Operario", email="felipe@sgt.cl"),
            dict(rut="10100006-6", nombre="Claudia",  apellido1="Fernández",empresa_id=e1.id, servicio_id=s_pronto.id, cargo="Cajera", email="claudia@sgt.cl"),
        ]
        for t_data in trabajadores:
            db.session.add(Trabajador(**t_data))
        db.session.commit()

        # ─── USUARIO ADMIN ───────────────────────────────────────────────────
        print("🔐 Creando usuario administrador...")
        admin = Usuario(
            rut="99999999-9",
            nombre="Admin",
            apellidos="Sistema",
            email="admin@sgt.cl",
            password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
            rol_id=rol_super.id,
        )
        db.session.add(admin)
        db.session.commit()

        print("=" * 50)
        print("✅ Seed simplificado completado con éxito.")
        print("=" * 50)

if __name__ == "__main__":
    seed()

"""
seed.py - Script para poblar la base de datos SGT con datos iniciales de prueba.
Ejecutar desde la raíz del proyecto: python app/seed.py
ADVERTENCIA: Borra y recrea todos los datos existentes.
"""
import sys
import os
# Agregar la raíz del proyecto al path para que encuentre el paquete 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.core import Region, Comuna, Feriado
from app.models.auth import Rol, Menu, RolMenu, Usuario
from app.models.business import Cliente, Empresa, Servicio, Turno, Trabajador, TrabajadorPreferencia
from datetime import date, time
import hashlib

app = create_app()

def seed():
    with app.app_context():
        print("🗑️  Limpiando base de datos...")
        db.drop_all()
        db.create_all()
        print("✅ Tablas creadas.\n")

        # ─── REGIONES ────────────────────────────────────────────────────────
        print("🌎 Insertando Regiones...")
        rm  = Region(codigo="RM",   descripcion="Región Metropolitana de Santiago")
        v   = Region(codigo="V",    descripcion="Región de Valparaíso")
        viii = Region(codigo="VIII", descripcion="Región del Biobío")
        ix  = Region(codigo="IX",   descripcion="Región de La Araucanía")
        db.session.add_all([rm, v, viii, ix])
        db.session.commit()
        print(f"   ✔ {Region.query.count()} regiones.\n")

        # ─── COMUNAS ─────────────────────────────────────────────────────────
        print("🏙️  Insertando Comunas...")
        comunas = [
            # Metropolitana
            Comuna(codigo="STGO",   descripcion="Santiago",           region_id=rm.id),
            Comuna(codigo="PROV",   descripcion="Providencia",        region_id=rm.id),
            Comuna(codigo="MAIP",   descripcion="Maipú",              region_id=rm.id),
            # Valparaíso
            Comuna(codigo="VALPO",  descripcion="Valparaíso",         region_id=v.id),
            Comuna(codigo="VIÑA",   descripcion="Viña del Mar",       region_id=v.id),
            # Biobío
            Comuna(codigo="CONC",   descripcion="Concepción",         region_id=viii.id),
            # Araucanía
            Comuna(codigo="TEMUCO", descripcion="Temuco",             region_id=ix.id),
        ]
        db.session.add_all(comunas)
        db.session.commit()
        c_stgo, c_prov, c_maip, c_valpo, c_viña, c_conc, c_temuco = comunas
        print(f"   ✔ {Comuna.query.count()} comunas.\n")

        # ─── FERIADOS ────────────────────────────────────────────────────────
        print("📅 Insertando Feriados...")
        feriados = [
            Feriado(fecha=date(2025, 1, 1),  descripcion="Año Nuevo"),
            Feriado(fecha=date(2025, 5, 1),  descripcion="Día del Trabajador"),
            Feriado(fecha=date(2025, 9, 18), descripcion="Fiestas Patrias"),
            Feriado(fecha=date(2025, 9, 19), descripcion="Día del Ejército"),
            Feriado(fecha=date(2025, 12, 25), descripcion="Navidad"),
        ]
        db.session.add_all(feriados)
        db.session.commit()
        print(f"   ✔ {Feriado.query.count()} feriados.\n")

        # ─── ROLES ───────────────────────────────────────────────────────────
        print("🎭 Insertando Roles...")
        rol_super   = Rol(descripcion="Super Admin")
        rol_cliente = Rol(descripcion="Cliente")
        rol_admin   = Rol(descripcion="Administrador")
        rol_visor   = Rol(descripcion="Visor")
        db.session.add_all([rol_super, rol_cliente, rol_admin, rol_visor])
        db.session.commit()
        print(f"   ✔ {Rol.query.count()} roles.\n")

        # ─── MENÚS ───────────────────────────────────────────────────────────
        print("📋 Insertando Menús...")
        menus_data = [
            "Dashboard", "Trabajadores", "Turnos", "Planificación",
            "Clientes", "Usuarios", "Empresas", "Servicios",
            "Regiones", "Comunas", "Feriados", "Roles", "Menús", "Simulación",
        ]
        menus = [Menu(nombre=m) for m in menus_data]
        db.session.add_all(menus)
        db.session.commit()
        print(f"   ✔ {Menu.query.count()} menús.\n")

        # ─── CLIENTES ────────────────────────────────────────────────────────
        print("👤 Insertando Clientes...")
        c1 = Cliente(rut="11111111-1", nombre="Juan",    apellidos="Pérez González",  email="juan.perez@holding.cl")
        c2 = Cliente(rut="22222222-2", nombre="María",   apellidos="Gómez Fuentes",   email="maria.gomez@copec.cl")
        c3 = Cliente(rut="33333333-3", nombre="Roberto", apellidos="Soto Valdivia",   email="roberto.soto@primax.cl")
        db.session.add_all([c1, c2, c3])
        db.session.commit()
        print(f"   ✔ {Cliente.query.count()} clientes.\n")

        # ─── EMPRESAS ────────────────────────────────────────────────────────
        # c1 (Juan Pérez) → 2 empresas | c2 y c3 → 1 empresa cada uno
        print("🏢 Insertando Empresas...")
        e1 = Empresa(rut="76111111-1", razon_social="Holding Norte SpA",    cliente_id=c1.id, comuna_id=c_stgo.id,  direccion="Av. Providencia 1234")
        e2 = Empresa(rut="76222222-2", razon_social="Holding Sur SpA",      cliente_id=c1.id, comuna_id=c_maip.id,  direccion="Av. Pajaritos 5678")
        e3 = Empresa(rut="76333333-3", razon_social="Copec Viña del Mar",   cliente_id=c2.id, comuna_id=c_viña.id,  direccion="Av. Marina 100")
        e4 = Empresa(rut="76444444-4", razon_social="Primax Concepción",    cliente_id=c3.id, comuna_id=c_conc.id,  direccion="Av. Libertad 999")
        db.session.add_all([e1, e2, e3, e4])
        db.session.commit()
        print(f"   ✔ {Empresa.query.count()} empresas.\n")

        # ─── SERVICIOS ───────────────────────────────────────────────────────
        print("⚙️  Insertando Servicios...")
        s_pista   = Servicio(descripcion="Pista Combustible")
        s_pronto  = Servicio(descripcion="Tienda Pronto")
        s_lavado  = Servicio(descripcion="Lavado de Autos")
        s_caja    = Servicio(descripcion="Caja / Cobranza")
        s_tienda  = Servicio(descripcion="Tienda Conveniencia")
        db.session.add_all([s_pista, s_pronto, s_lavado, s_caja, s_tienda])
        db.session.commit()

        # Asociar servicios a empresas (muchos a muchos)
        e1.servicios = [s_pista, s_pronto, s_lavado]
        e2.servicios = [s_pista, s_caja]
        e3.servicios = [s_pista, s_pronto, s_tienda]
        e4.servicios = [s_pista, s_lavado, s_caja]
        db.session.commit()
        print(f"   ✔ {Servicio.query.count()} servicios.\n")

        # ─── TURNOS ──────────────────────────────────────────────────────────
        print("🕐 Insertando Turnos por empresa...")
        turnos = [
            # Holding Norte (e1)
            Turno(empresa_id=e1.id, nombre="Mañana",      abreviacion="M",  hora_inicio=time(7,0),  hora_fin=time(15,0), color="#3498db", dotacion_diaria=3),
            Turno(empresa_id=e1.id, nombre="Tarde",       abreviacion="T",  hora_inicio=time(15,0), hora_fin=time(23,0), color="#e67e22", dotacion_diaria=3),
            Turno(empresa_id=e1.id, nombre="Noche",       abreviacion="N",  hora_inicio=time(23,0), hora_fin=time(7,0),  color="#2c3e50", dotacion_diaria=2),
            # Holding Sur (e2)
            Turno(empresa_id=e2.id, nombre="Apertura",    abreviacion="A",  hora_inicio=time(6,0),  hora_fin=time(14,0), color="#27ae60", dotacion_diaria=2),
            Turno(empresa_id=e2.id, nombre="Cierre",      abreviacion="C",  hora_inicio=time(14,0), hora_fin=time(22,0), color="#8e44ad", dotacion_diaria=2),
            # Copec Viña (e3)
            Turno(empresa_id=e3.id, nombre="Mañana",      abreviacion="M",  hora_inicio=time(8,0),  hora_fin=time(16,0), color="#3498db", dotacion_diaria=4),
            Turno(empresa_id=e3.id, nombre="Tarde",       abreviacion="T",  hora_inicio=time(16,0), hora_fin=time(0,0),  color="#e67e22", dotacion_diaria=4),
            Turno(empresa_id=e3.id, nombre="Intermedio",  abreviacion="I",  hora_inicio=time(11,0), hora_fin=time(19,0), color="#1abc9c", dotacion_diaria=2),
            # Primax Concepción (e4)
            Turno(empresa_id=e4.id, nombre="Diurno",      abreviacion="D",  hora_inicio=time(7,0),  hora_fin=time(19,0), color="#f39c12", dotacion_diaria=3),
            Turno(empresa_id=e4.id, nombre="Nocturno",    abreviacion="Nc", hora_inicio=time(19,0), hora_fin=time(7,0),  color="#2c3e50", dotacion_diaria=2),
        ]
        db.session.add_all(turnos)
        db.session.commit()
        print(f"   ✔ {Turno.query.count()} turnos.\n")

        # ─── TRABAJADORES ────────────────────────────────────────────────────
        print("👷 Insertando Trabajadores...")
        trabajadores_data = [
            # Holding Norte (e1) - servicio: Pista
            dict(rut="10100001-1", nombre="Carlos",   apellido1="Muñoz",    apellido2="Rojas",    empresa_id=e1.id, servicio_id=s_pista.id,  cargo="Operario Pista",    email="carlos.munoz@sgt.cl",    tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10100002-2", nombre="Ana",      apellido1="Torres",   apellido2="Vega",     empresa_id=e1.id, servicio_id=s_pronto.id, cargo="Cajera Pronto",     email="ana.torres@sgt.cl",      tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10100003-3", nombre="Diego",    apellido1="Salinas",  apellido2="Mora",     empresa_id=e1.id, servicio_id=s_lavado.id, cargo="Técnico Lavado",    email="diego.salinas@sgt.cl",   tipo_contrato="part-time",  horas_semanales=30),
            # Holding Sur (e2) - servicio: Pista / Caja
            dict(rut="10200001-1", nombre="Valentina",apellido1="Reyes",    apellido2="Navarro",  empresa_id=e2.id, servicio_id=s_pista.id,  cargo="Operaria Pista",    email="valentina.reyes@sgt.cl", tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10200002-2", nombre="Felipe",   apellido1="Contreras",apellido2="Lagos",    empresa_id=e2.id, servicio_id=s_caja.id,   cargo="Cajero",            email="felipe.contreras@sgt.cl",tipo_contrato="full-time",  horas_semanales=45),
            # Copec Viña (e3)
            dict(rut="10300001-1", nombre="Claudia",  apellido1="Fernández",apellido2="Soto",     empresa_id=e3.id, servicio_id=s_pista.id,  cargo="Supervisora Pista", email="claudia.f@sgt.cl",       tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10300002-2", nombre="Rodrigo",  apellido1="Vargas",   apellido2="Fuentes",  empresa_id=e3.id, servicio_id=s_pronto.id, cargo="Vendedor Pronto",   email="rodrigo.v@sgt.cl",       tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10300003-3", nombre="Javiera",  apellido1="Castro",   apellido2="Mena",     empresa_id=e3.id, servicio_id=s_tienda.id, cargo="Encargada Tienda",  email="javiera.c@sgt.cl",       tipo_contrato="part-time",  horas_semanales=30),
            # Primax Concepción (e4)
            dict(rut="10400001-1", nombre="Sebastián",apellido1="Pizarro",  apellido2="Ríos",     empresa_id=e4.id, servicio_id=s_pista.id,  cargo="Operario Pista",    email="sebastian.p@sgt.cl",     tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10400002-2", nombre="Patricia", apellido1="Ibáñez",   apellido2="Campos",   empresa_id=e4.id, servicio_id=s_caja.id,   cargo="Cajera",            email="patricia.i@sgt.cl",      tipo_contrato="full-time",  horas_semanales=45),
            dict(rut="10400003-3", nombre="Gonzalo",  apellido1="Espinoza", apellido2="Leal",     empresa_id=e4.id, servicio_id=s_lavado.id, cargo="Técnico Lavado",    email="gonzalo.e@sgt.cl",       tipo_contrato="part-time",  horas_semanales=30),
        ]
        for td in trabajadores_data:
            db.session.add(Trabajador(**td))
        db.session.commit()
        print(f"   ✔ {Trabajador.query.count()} trabajadores.\n")

        # ─── USUARIO ADMIN ───────────────────────────────────────────────────
        print("🔐 Creando usuario administrador...")
        admin = Usuario(
            rut="99999999-9",
            nombre="Admin",
            apellidos="Sistema SGT",
            email="admin@sgt.cl",
            password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
            rol_id=rol_super.id,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"   ✔ Usuario admin@sgt.cl creado (pass: admin123).\n")

        print("=" * 50)
        print("✅ Seed completado exitosamente.")
        print(f"   Regiones: {Region.query.count()}")
        print(f"   Comunas:  {Comuna.query.count()}")
        print(f"   Clientes: {Cliente.query.count()}")
        print(f"   Empresas: {Empresa.query.count()}")
        print(f"   Servicios:{Servicio.query.count()}")
        print(f"   Turnos:   {Turno.query.count()}")
        print(f"   Workers:  {Trabajador.query.count()}")
        print("=" * 50)

if __name__ == "__main__":
    seed()

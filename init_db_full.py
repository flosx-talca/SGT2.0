"""
SGT 2.1 - Script de Inicialización de Base de Datos
--------------------------------------------------
Este script realiza la migración y carga de datos iniciales.

Comandos para configurar el entorno:

Windows:
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt

Linux/macOS:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Ejecución:
    python init_db_full.py
"""
import os
import sys
from datetime import datetime, time
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.auth import Rol, Menu, RolMenu, Usuario
from app.models.business import (
    TurnoPlantilla, TipoAusenciaPlantilla, ParametroLegal, 
    CategoriaAusencia
)
from app.models.core import Region, Comuna

def init_db():
    app = create_app()
    with app.app_context():
        print("--- Iniciando Inicialización de Base de Datos SGT 2.1 ---")
        
        # 1. Ejecutar migraciones
        print("Ejecutando migraciones (flask db upgrade)...")
        os.system("flask db upgrade")
        
        # 2. Roles Base
        print("Creando roles base...")
        roles_data = [
            {'descripcion': 'Super Admin'},
            {'descripcion': 'Cliente'},
            {'descripcion': 'Administrador'}
        ]
        roles_objs = {}
        for r in roles_data:
            obj = Rol.query.filter_by(descripcion=r['descripcion']).first()
            if not obj:
                obj = Rol(descripcion=r['descripcion'])
                db.session.add(obj)
                db.session.flush()
            roles_objs[r['descripcion']] = obj

        # 3. Menús Base
        print("Creando menús base...")
        menus_data = [
            {'nombre': 'Dashboard', 'endpoint': 'main.index', 'icono': 'fa fa-th-large', 'orden': 1, 'es_base': True},
            {'nombre': 'Trabajadores', 'endpoint': 'trabajador.index', 'icono': 'fa fa-users', 'orden': 2, 'es_base': True},
            {'nombre': 'Turnos', 'endpoint': 'turno.index', 'icono': 'fa fa-clock', 'orden': 3, 'es_base': True},
            {'nombre': 'Ausencias', 'endpoint': 'ausencia.index', 'icono': 'fa fa-calendar-times', 'orden': 4, 'es_base': True},
            {'nombre': 'Tipos de Ausencia', 'endpoint': 'tipo_ausencia.index', 'icono': 'fa fa-user-minus', 'orden': 5, 'es_base': True},
            {'nombre': 'Planificación', 'endpoint': 'main.planificacion', 'icono': 'fa fa-calendar-alt', 'orden': 6, 'es_base': True},
            {'nombre': 'Simulación', 'endpoint': 'main.simulacion', 'icono': 'fa fa-robot', 'orden': 7, 'es_base': True},
            
            {'nombre': 'Clientes', 'endpoint': 'cliente.index', 'icono': 'fa fa-handshake', 'orden': 20, 'es_base': False},
            {'nombre': 'Empresas', 'endpoint': 'empresa.index', 'icono': 'fa fa-building', 'orden': 21, 'es_base': False},
            {'nombre': 'Servicios', 'endpoint': 'servicio.index', 'icono': 'fa fa-concierge-bell', 'orden': 22, 'es_base': False},
            {'nombre': 'Usuarios', 'endpoint': 'usuario.index', 'icono': 'fa fa-users-cog', 'orden': 23, 'es_base': False},
            {'nombre': 'Roles', 'endpoint': 'rol.index', 'icono': 'fa fa-id-badge', 'orden': 24, 'es_base': False},
            {'nombre': 'Menús', 'endpoint': 'menu.index', 'icono': 'fa fa-list', 'orden': 25, 'es_base': False},
            
            {'nombre': 'Regiones', 'endpoint': 'region.index', 'icono': 'fa fa-map-marked-alt', 'orden': 30, 'es_base': False},
            {'nombre': 'Comunas', 'endpoint': 'comuna.index', 'icono': 'fa fa-map-pin', 'orden': 31, 'es_base': False},
            {'nombre': 'Feriados', 'endpoint': 'feriado.index', 'icono': 'fa fa-umbrella-beach', 'orden': 32, 'es_base': False},
            
            {'nombre': 'Reglas Empresa', 'endpoint': 'regla_empresa.index', 'icono': 'fa fa-briefcase', 'orden': 40, 'es_base': False},
            {'nombre': 'Reglas Familia', 'endpoint': 'main.reglas_familias', 'icono': 'fa fa-layer-group', 'orden': 41, 'es_base': False},
            {'nombre': 'Reglas Generales', 'endpoint': 'regla.index', 'icono': 'fa fa-cogs', 'orden': 42, 'es_base': False},
            {'nombre': 'Configuración Reglas', 'endpoint': 'main.reglas_config', 'icono': 'fa fa-sliders-h', 'orden': 43, 'es_base': False},
            {'nombre': 'Parámetros Legales', 'endpoint': 'parametro_legal.index', 'icono': 'fa fa-gavel', 'orden': 44, 'es_base': False},
        ]
        
        menu_objs = {}
        for m in menus_data:
            obj = Menu.query.filter_by(endpoint=m['endpoint']).first()
            if not obj:
                obj = Menu(**m)
                db.session.add(obj)
                db.session.flush()
            else:
                # Actualizar datos existentes por si acaso
                obj.nombre = m['nombre']
                obj.icono = m['icono']
                obj.orden = m['orden']
                obj.es_base = m['es_base']
            menu_objs[m['endpoint']] = obj

        # 4. Asignar Menús a Roles (RolMenu)
        print("Asignando permisos a roles...")
        
        # Mapeo de qué menús van a qué roles (por endpoint)
        role_permissions = {
            'Super Admin': [m['endpoint'] for m in menus_data], # Todos los menús
            'Administrador': [
                'main.index', 'trabajador.index', 'turno.index', 
                'ausencia.index', 'tipo_ausencia.index', 
                'main.planificacion', 'main.simulacion'
            ],
            'Cliente': [
                'main.index', 'trabajador.index', 'turno.index', 
                'ausencia.index', 'tipo_ausencia.index', 
                'main.planificacion', 'main.simulacion'
            ]
        }

        for rol_nombre, endpoints in role_permissions.items():
            rol_obj = roles_objs.get(rol_nombre)
            if not rol_obj: continue
            
            for ep in endpoints:
                menu_obj = menu_objs.get(ep)
                if not menu_obj: continue
                
                rm = RolMenu.query.filter_by(rol_id=rol_obj.id, menu_id=menu_obj.id).first()
                if not rm:
                    db.session.add(RolMenu(
                        rol_id=rol_obj.id,
                        menu_id=menu_obj.id,
                        puede_crear=True,
                        puede_editar=True,
                        puede_eliminar=True
                    ))

        # 5. Usuario Super Admin (Orlando)
        print("Creando usuario administrador...")
        user_admin = Usuario.query.filter_by(rut='15774247-7').first()
        if not user_admin:
            user_admin = Usuario(
                rut='15774247-7',
                nombre='Orlando',
                apellidos='Admin',
                email='orozasi@gmail.com',
                password_hash=generate_password_hash('admin123'),
                rol_id=super_admin_rol.id,
                activo=True
            )
            db.session.add(user_admin)
        else:
            user_admin.rol_id = super_admin_rol.id # Asegurar que es Super Admin

        # 6. Parámetros Legales y de Optimización
        print("Creando parámetros legales y de optimización...")
        legales = [
            # Jornada Ordinaria
            {'codigo': 'MAX_HRS_SEMANA_FULL', 'valor': 42.0, 'categoria': 'Jornada', 'descripcion': 'Horas semanales máximas full-time (Ley 21.561)'},
            {'codigo': 'MAX_HRS_DIA_FULL', 'valor': 10.0, 'categoria': 'Jornada', 'descripcion': 'Jornada diaria máxima full-time (Art. 28 CT)'},
            {'codigo': 'MIN_DIAS_SEMANA_FULL', 'valor': 5.0, 'categoria': 'Jornada', 'descripcion': 'Días mínimos distribución semanal full-time (Art. 28 CT)'},
            {'codigo': 'MAX_DIAS_SEMANA_FULL', 'valor': 6.0, 'categoria': 'Jornada', 'descripcion': 'Días máximos distribución semanal full-time (Art. 28 CT)'},
            
            # Jornada Parcial
            {'codigo': 'MAX_HRS_SEMANA_PART_TIME_30', 'valor': 30.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada parcial máxima 30h (Art. 40 bis CT)'},
            {'codigo': 'MAX_HRS_SEMANA_PART_TIME_20', 'valor': 20.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada reducida máxima 20h'},
            {'codigo': 'MAX_HRS_DIA_PART_TIME', 'valor': 10.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada diaria máxima part-time (Art. 40 bis CT)'},
            {'codigo': 'MAX_DIAS_SEMANA_PART', 'valor': 5.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Días máximos distribución semanal part-time'},
            
            # Domingos y Descansos
            {'codigo': 'UMBRAL_DIAS_DOMINGO_OBLIGATORIO', 'valor': 5.0, 'categoria': 'Descansos', 'descripcion': 'Días/sem mínimos para que aplique compensación dominical'},
            {'codigo': 'MIN_DOMINGOS_LIBRES_MES', 'valor': 2.0, 'categoria': 'Descansos', 'descripcion': 'Domingos libres mínimos/mes cuando aplica'},
            {'codigo': 'MAX_DIAS_CONSECUTIVOS', 'valor': 6.0, 'categoria': 'Descansos', 'descripcion': 'Días consecutivos máximos de trabajo (Art. 38 CT)'},
            {'codigo': 'MIN_DESCANSO_ENTRE_TURNOS_HRS', 'valor': 12.0, 'categoria': 'Descansos', 'descripcion': 'Horas mínimas de descanso entre dos turnos'},
            
            # Semanas Cortas
            {'codigo': 'SEMANA_CORTA_UMBRAL_DIAS', 'valor': 5.0, 'categoria': 'Semanas Cortas', 'descripcion': 'Días mínimos para considerar semana completa'},
            {'codigo': 'SEMANA_CORTA_PRORRATEO', 'valor': 1.0, 'categoria': 'Semanas Cortas', 'descripcion': '1 = prorratear horas proporcionales en semana corta'},
            
            # Solver / Optimización (Pesos SGT 2.1)
            {'codigo': 'W_DEFICIT', 'valor': 10000000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por turno no cubierto (Prioridad #1)'},
            {'codigo': 'W_EXCESO', 'valor': 100000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por sobre-dotación'},
            {'codigo': 'W_EQUIDAD', 'valor': 1000000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por desigualdad de carga entre trabajadores'},
            {'codigo': 'W_META', 'valor': 50000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por desviación de la meta mensual'},
            {'codigo': 'W_EXCESO_HORAS', 'valor': 20000000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por exceso de jornada semanal (Muy alta)'},
            {'codigo': 'W_REWARD', 'valor': 10000.0, 'categoria': 'Optimizacion', 'descripcion': 'Incentivo por asignación estándar'},
            {'codigo': 'W_NOCHE_REWARD', 'valor': 20000.0, 'categoria': 'Optimizacion', 'descripcion': 'Incentivo por cubrir turnos nocturnos'},
            {'codigo': 'W_CAMBIO_TURNO', 'valor': 150.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por cambio de turno entre días'},
            {'codigo': 'W_TURNO_DOMINANTE', 'valor': 80.0, 'categoria': 'Optimizacion', 'descripcion': 'Bonus por mantener un turno dominante'},
            {'codigo': 'W_NO_PREFERENTE', 'valor': 500.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización por no asignar turno preferente'},
            {'codigo': 'DURACION_TURNO_PROMEDIO', 'valor': 8.0, 'categoria': 'Optimizacion', 'descripcion': 'Duración estimada de turno para cálculos de capacidad'},
            {'codigo': 'SOLVER_TIMEOUT_SEG', 'valor': 60.0, 'categoria': 'Optimizacion', 'descripcion': 'Tiempo máximo de ejecución del motor (segundos)'},
            {'codigo': 'MAX_HRS_SEMANA_FULL', 'valor': 42.0, 'categoria': 'Jornada', 'descripcion': 'Horas semanales máximas (Fallback)'},
        ]
        for l in legales:
            p = ParametroLegal.query.filter_by(codigo=l['codigo']).first()
            if not p:
                db.session.add(ParametroLegal(**l))
            else:
                # Actualizar valores si ya existen (opcional)
                p.valor = l['valor']
                p.categoria = l['categoria']
                p.descripcion = l['descripcion']

        # 7. Turnos Plantilla
        print("Creando plantillas de turnos...")
        turnos_p = [
            {'nombre': 'Mañana', 'abreviacion': 'M', 'hora_inicio': time(7,0), 'hora_fin': time(15,0), 'color': '#18bc9c'},
            {'nombre': 'Tarde', 'abreviacion': 'T', 'hora_inicio': time(15,0), 'hora_fin': time(23,0), 'color': '#3498db'},
            {'nombre': 'Noche', 'abreviacion': 'N', 'hora_inicio': time(23,0), 'hora_fin': time(7,0), 'color': '#34495e', 'es_nocturno': True},
            {'nombre': 'Intermedio', 'abreviacion': 'I', 'hora_inicio': time(10,0), 'hora_fin': time(18,0), 'color': '#f39c12'},
        ]
        for tp in turnos_p:
            if not TurnoPlantilla.query.filter_by(abreviacion=tp['abreviacion']).first():
                db.session.add(TurnoPlantilla(**tp))

        # 8. Tipos de Ausencia y Restricciones Plantilla
        print("Creando plantillas de ausencias y restricciones...")
        from app.models.enums import RestrictionType
        ausencias_p = [
            # Ausencias Físicas (Días)
            {'nombre': 'Vacaciones', 'abreviacion': 'VAC', 'color': '#2ecc71', 'categoria': CategoriaAusencia.AUSENCIA},
            {'nombre': 'Licencia Médica', 'abreviacion': 'LIC', 'color': '#e74c3c', 'categoria': CategoriaAusencia.AUSENCIA},
            {'nombre': 'Permiso Administrativo', 'abreviacion': 'PER', 'color': '#9b59b6', 'categoria': CategoriaAusencia.AUSENCIA},
            {'nombre': 'Día Libre Fijo', 'abreviacion': 'LIB', 'color': '#95a5a6', 'categoria': CategoriaAusencia.AUSENCIA},
            
            # Restricciones Lógicas / Solver (Turnos y Reglas)
            {'nombre': 'Turno Fijo', 'abreviacion': 'TFIJ', 'color': '#f1c40f', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_FIJO},
            {'nombre': 'Turno Preferente', 'abreviacion': 'TPRE', 'color': '#e67e22', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_PREFERENTE},
            {'nombre': 'Solo este Turno', 'abreviacion': 'SOLO', 'color': '#3498db', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.SOLO_TURNO},
            {'nombre': 'Excluir Turno', 'abreviacion': 'EXCL', 'color': '#34495e', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.EXCLUIR_TURNO},
        ]
        for ap in ausencias_p:
            obj = TipoAusenciaPlantilla.query.filter_by(abreviacion=ap['abreviacion']).first()
            if not obj:
                db.session.add(TipoAusenciaPlantilla(**ap))
            else:
                obj.categoria = ap.get('categoria', CategoriaAusencia.AUSENCIA)
                obj.tipo_restriccion = ap.get('tipo_restriccion')

        # 9. Regiones y Comunas (Ejemplo básico si no existen)
        print("Verificando geografía básica...")
        if not Region.query.first():
            r1 = Region(id=1, descripcion='Metropolitana', codigo='RM')
            db.session.add(r1)
            db.session.flush()
            if not Comuna.query.filter_by(descripcion='Santiago').first():
                db.session.add(Comuna(descripcion='Santiago', region_id=r1.id, codigo='13101'))

        db.session.commit()
        print("\n--- ¡Inicialización Exitosa! ---")
        print("Usuario: orozasi@gmail.com / Pass: admin123")

if __name__ == '__main__':
    # Verificar si el entorno virtual está activo
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("\n" + "!"*60)
        print("ADVERTENCIA: No se detectó un entorno virtual activo.")
        print("Se recomienda activar el entorno antes de continuar:")
        print("  Windows: .\\venv\\Scripts\\activate")
        print("  Linux/macOS: source venv/bin/activate")
        print("!"*60 + "\n")
        
        # Opcional: Podríamos forzar la salida si es crítico
        # sys.exit(1)

    init_db()

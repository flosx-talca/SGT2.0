"""
SGT 2.1 - Script de Inicialización Maestra
--------------------------------------------------
Este script realiza la carga completa de datos maestros, configuraciones legales,
plantillas universales y asegura el acceso del administrador.
"""
import os
import sys
import json
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
        print("--- Iniciando Inicialización Maestra SGT 2.1 ---")
        
        # 1. Asegurar Roles
        print("Creando roles base...")
        roles_data = ['Super Admin', 'Cliente', 'Administrador']
        roles_objs = {}
        for r_desc in roles_data:
            obj = Rol.query.filter_by(descripcion=r_desc).first()
            if not obj:
                obj = Rol(descripcion=r_desc)
                db.session.add(obj)
                db.session.flush()
            roles_objs[r_desc] = obj

        # 2. Menús del Sistema
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
            {'nombre': 'Reglas Generales', 'endpoint': 'regla.index', 'icono': 'fa fa-cogs', 'orden': 42, 'es_base': False},
            {'nombre': 'Parámetros Legales', 'endpoint': 'parametro_legal.index', 'icono': 'fa fa-gavel', 'orden': 44, 'es_base': False},
        ]
        menu_objs = {}
        for m in menus_data:
            obj = Menu.query.filter_by(endpoint=m['endpoint']).first()
            if not obj:
                obj = Menu(**m)
                db.session.add(obj)
                db.session.flush()
            menu_objs[m['endpoint']] = obj

        # 3. Permisos (RolMenu)
        print("Asignando permisos...")
        for rol_nombre, endpoints in {
            'Super Admin': [m['endpoint'] for m in menus_data],
            'Administrador': ['main.index', 'trabajador.index', 'turno.index', 'ausencia.index', 'tipo_ausencia.index', 'main.planificacion'],
            'Cliente': ['main.index', 'trabajador.index', 'turno.index', 'ausencia.index', 'tipo_ausencia.index', 'main.planificacion']
        }.items():
            rol_obj = roles_objs.get(rol_nombre)
            for ep in endpoints:
                menu_obj = menu_objs.get(ep)
                if rol_obj and menu_obj:
                    rm = RolMenu.query.filter_by(rol_id=rol_obj.id, menu_id=menu_obj.id).first()
                    if not rm:
                        db.session.add(RolMenu(rol_id=rol_obj.id, menu_id=menu_obj.id, puede_crear=True, puede_editar=True, puede_eliminar=True))

        # 4. Usuario Administrador Asegurado
        print("Asegurando usuario administrador...")
        rol_super = roles_objs['Super Admin']
        user_admin = Usuario.query.filter_by(rut='15774247-7').first()
        if not user_admin:
            user_admin = Usuario(
                rut='15774247-7', nombre='Orlando', apellidos='Admin',
                email='orozasi@gmail.com', password_hash=generate_password_hash('admin123'),
                rol_id=rol_super.id, activo=True
            )
            db.session.add(user_admin)
        else:
            user_admin.rol_id = rol_super.id
            user_admin.email = 'orozasi@gmail.com'

        # 5. Los 43 Parámetros Legales y de Optimización
        print("Cargando 43 parámetros de configuración...")
        legales = [
            # Jornada
            {'codigo': 'MAX_HRS_SEMANA_FULL', 'valor': 42.0, 'categoria': 'Jornada', 'descripcion': 'Horas semanales maximas full-time (Ley 21.561)'},
            {'codigo': 'MAX_HRS_DIA_FULL', 'valor': 10.0, 'categoria': 'Jornada', 'descripcion': 'Jornada diaria maxima full-time (Art. 28 CT)'},
            {'codigo': 'MIN_DIAS_SEMANA_FULL', 'valor': 5.0, 'categoria': 'Jornada', 'descripcion': 'Dias minimos distribucion semanal full-time (Art. 28 CT)'},
            {'codigo': 'MAX_DIAS_SEMANA_FULL', 'valor': 6.0, 'categoria': 'Jornada', 'descripcion': 'Dias maximos distribucion semanal full-time (Art. 28 CT)'},
            
            # Jornada Parcial
            {'codigo': 'MAX_HRS_SEMANA_PART_TIME_30', 'valor': 30.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada parcial maxima 30h (Art. 40 bis CT)'},
            {'codigo': 'MAX_HRS_SEMANA_PART_TIME_20', 'valor': 20.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada reducida maxima 20h'},
            {'codigo': 'MAX_HRS_DIA_PART_TIME', 'valor': 10.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Jornada diaria maxima part-time (Art. 40 bis CT)'},
            {'codigo': 'MAX_DIAS_SEMANA_PART', 'valor': 5.0, 'categoria': 'Jornada Parcial', 'descripcion': 'Dias maximos distribucion semanal part-time'},
            
            # Descansos
            {'codigo': 'MIN_DOMINGOS_LIBRES_MES', 'valor': 2.0, 'categoria': 'Descansos', 'descripcion': 'Domingos libres minimos/mes cuando aplica'},
            {'codigo': 'MIN_DESCANSO_ENTRE_TURNOS_HRS', 'valor': 12.0, 'categoria': 'Descansos', 'descripcion': 'Horas minimas de descanso entre dos turnos'},
            {'codigo': 'MAX_DIAS_CONSECUTIVOS', 'valor': 6.0, 'categoria': 'Descansos', 'descripcion': 'Dias consecutivos maximos de trabajo (Art. 38 CT)'},
            {'codigo': 'UMBRAL_DIAS_DOMINGO_OBLIGATORIO', 'valor': 5.0, 'categoria': 'Descansos', 'descripcion': 'Dias trabajados para exigir domingos libres'},
            
            # Semanas Cortas
            {'codigo': 'SEMANA_CORTA_UMBRAL_DIAS', 'valor': 5.0, 'categoria': 'Semanas Cortas', 'descripcion': 'Umbral de días para considerar semana corta'},
            {'codigo': 'SEMANA_CORTA_PRORRATEO', 'valor': 1.0, 'categoria': 'Semanas Cortas', 'descripcion': '1 si aplica prorrateo en semana corta, 0 si no'},
            
            # Planificación / Estabilidad
            {'codigo': 'MIN_HRS_TURNO_ABSOLUTO', 'valor': 4.0, 'categoria': 'Planificación', 'descripcion': 'Mínimo de horas por turno según ley'},
            {'codigo': 'MIN_HRS_TURNO_CON_COLACION', 'valor': 6.0, 'categoria': 'Planificación', 'descripcion': 'Mínimo de horas para tener derecho a colación'},
            {'codigo': 'MIN_COLACION_MIN', 'valor': 30.0, 'categoria': 'Planificación', 'descripcion': 'Mínimo de minutos de colación'},
            {'codigo': 'MAX_COLACION_MIN', 'valor': 120.0, 'categoria': 'Planificación', 'descripcion': 'Máximo de minutos de colación'},
            {'codigo': 'HORA_INICIO_NOCTURNO', 'valor': 21.0, 'categoria': 'Planificación', 'descripcion': 'Hora en que inicia el tramo nocturno (21:00)'},
            {'codigo': 'HORA_FIN_NOCTURNO', 'valor': 6.0, 'categoria': 'Planificación', 'descripcion': 'Hora en que termina el tramo nocturno (06:00)'},
            {'codigo': 'DOMINGOS_EXTRA_ANUALES_ART38BIS', 'valor': 7.0, 'categoria': 'Planificación', 'descripcion': 'Domingos extra al año según Art 38 Bis'},
            {'codigo': 'MAX_DOMINGOS_SUSTITUIBLES_SABADO', 'valor': 1.0, 'categoria': 'Planificación', 'descripcion': 'Domingos que pueden sustituirse por sábados'},
            {'codigo': 'COMP_PLAZO_DIAS_GENERAL', 'valor': 15.0, 'categoria': 'Planificación', 'descripcion': 'Plazo general para compensación'},
            {'codigo': 'COMP_PLAZO_DIAS_EXCEPTUADO', 'valor': 30.0, 'categoria': 'Planificación', 'descripcion': 'Plazo exceptuado para compensación'},
            {'codigo': 'ESTAB_MIN_DIAS_MISMO_TURNO', 'valor': 3.0, 'categoria': 'Planificación', 'descripcion': 'Mínimo de días en el mismo turno para estabilidad'},
            {'codigo': 'ESTAB_PENALTY_CAMBIO_TURNO', 'valor': 150.0, 'categoria': 'Planificación', 'descripcion': 'Penalización por cambio de turno'},
            {'codigo': 'ESTAB_PENALTY_TURNO_AISLADO', 'valor': 200.0, 'categoria': 'Planificación', 'descripcion': 'Penalización por turno aislado'},
            {'codigo': 'ESTAB_BONUS_TURNO_DOMINANTE', 'valor': 80.0, 'categoria': 'Planificación', 'descripcion': 'Bono por mantener turno dominante'},
            {'codigo': 'SOLVER_MAX_WORKERS', 'valor': 100.0, 'categoria': 'Planificación', 'descripcion': 'Máximo de trabajadores soportados por el solver'},
            {'codigo': 'SOFT_PENALTY_DIA_AISLADO', 'valor': 500.0, 'categoria': 'Planificación', 'descripcion': 'Penalización soft por día de trabajo aislado'},
            {'codigo': 'SOFT_PENALTY_DESCANSO_AISLADO', 'valor': 300.0, 'categoria': 'Planificación', 'descripcion': 'Penalización soft por día libre aislado'},
            {'codigo': 'SOFT_BONUS_BLOQUE_CONTINUO', 'valor': 1000.0, 'categoria': 'Planificación', 'descripcion': 'Bono por bloques continuos de trabajo'},
            {'codigo': 'PREF_MIN_DIAS_BLOQUE', 'valor': 2.0, 'categoria': 'Planificación', 'descripcion': 'Mínimo de días para bloque preferente'},
            {'codigo': 'PREF_MAX_DIAS_BLOQUE', 'valor': 6.0, 'categoria': 'Planificación', 'descripcion': 'Máximo de días para bloque preferente'},
            
            # Pesos del Motor
            {'codigo': 'W_DEFICIT', 'valor': 10000000.0, 'categoria': 'Planificación', 'descripcion': 'Costo por turno sin cubrir'},
            {'codigo': 'W_EXCESO', 'valor': 100000.0, 'categoria': 'Planificación', 'descripcion': 'Costo por exceso de cobertura'},
            {'codigo': 'W_EQUIDAD', 'valor': 1000000.0, 'categoria': 'Planificación', 'descripcion': 'Penalización equidad mensual'},
            {'codigo': 'W_META', 'valor': 50000.0, 'categoria': 'Planificación', 'descripcion': 'Penalización meta mensual'},
            {'codigo': 'W_REWARD', 'valor': 10000.0, 'categoria': 'Planificación', 'descripcion': 'Premio por cubrir turno'},
            {'codigo': 'W_NOCHE_REWARD', 'valor': 20000.0, 'categoria': 'Planificación', 'descripcion': 'Premio extra turno nocturno'},
            {'codigo': 'W_NO_PREFERENTE', 'valor': 500.0, 'categoria': 'Planificación', 'descripcion': 'Penalización turno no preferente'},
            {'codigo': 'W_CAMBIO_TURNO', 'valor': 150.0, 'categoria': 'Planificación', 'descripcion': 'Penalización cambio de turno'},
            {'codigo': 'W_TURNO_DOMINANTE', 'valor': 80.0, 'categoria': 'Planificación', 'descripcion': 'Bonus turno dominante'},
            
            # Optimización
            {'codigo': 'DURACION_TURNO_PROMEDIO', 'valor': 8.0, 'categoria': 'Optimizacion', 'descripcion': 'Duración estimada de turno'},
            {'codigo': 'SOLVER_TIMEOUT_SEG', 'valor': 60.0, 'categoria': 'Optimizacion', 'descripcion': 'Tiempo máximo solver'},
            {'codigo': 'W_EXCESO_HORAS', 'valor': 20000000.0, 'categoria': 'Optimizacion', 'descripcion': 'Penalización exceso jornada'},
        ]
        for l in legales:
            p = ParametroLegal.query.filter_by(codigo=l['codigo']).first()
            if not p:
                db.session.add(ParametroLegal(**l))
            else:
                p.valor = l['valor']
                p.categoria = l['categoria']
                p.descripcion = l['descripcion']

        # 6. Plantillas de Turnos
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

        # 7. Plantillas de Ausencias y Restricciones (es_base=True)
        print("Creando plantillas de ausencias y restricciones...")
        from app.models.enums import RestrictionType
        ausencias_p = [
            {'nombre': 'Vacaciones', 'abreviacion': 'VAC', 'color': '#2ecc71', 'categoria': CategoriaAusencia.AUSENCIA, 'es_base': True},
            {'nombre': 'Licencia Médica', 'abreviacion': 'LIC', 'color': '#e74c3c', 'categoria': CategoriaAusencia.AUSENCIA, 'es_base': True},
            {'nombre': 'Permiso Administrativo', 'abreviacion': 'PER', 'color': '#9b59b6', 'categoria': CategoriaAusencia.AUSENCIA, 'es_base': True},
            {'nombre': 'Día Libre Fijo', 'abreviacion': 'LIB', 'color': '#95a5a6', 'categoria': CategoriaAusencia.AUSENCIA, 'es_base': True},
            {'nombre': 'Turno Fijo', 'abreviacion': 'TFIJ', 'color': '#f1c40f', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_FIJO, 'es_base': True},
            {'nombre': 'Turno Preferente', 'abreviacion': 'TPRE', 'color': '#e67e22', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_PREFERENTE, 'es_base': True},
            {'nombre': 'Solo este Turno', 'abreviacion': 'SOLO', 'color': '#3498db', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.SOLO_TURNO, 'es_base': True},
            {'nombre': 'Excluir Turno', 'abreviacion': 'EXCL', 'color': '#34495e', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.EXCLUIR_TURNO, 'es_base': True},
        ]
        for ap in ausencias_p:
            obj = TipoAusenciaPlantilla.query.filter_by(abreviacion=ap['abreviacion']).first()
            if not obj:
                db.session.add(TipoAusenciaPlantilla(**ap))
            else:
                obj.es_base = True
                obj.categoria = ap['categoria']
                obj.tipo_restriccion = ap.get('tipo_restriccion')

        # 8. Geografía Base (16 Regiones de Chile)
        print("Cargando las 16 regiones de Chile...")
        regiones_data = [
            {'id': 15, 'descripcion': 'Arica y Parinacota', 'codigo': 'AP'},
            {'id': 1,  'descripcion': 'Tarapacá', 'codigo': 'TA'},
            {'id': 2,  'descripcion': 'Antofagasta', 'codigo': 'AN'},
            {'id': 3,  'descripcion': 'Atacama', 'codigo': 'AT'},
            {'id': 4,  'descripcion': 'Coquimbo', 'codigo': 'CO'},
            {'id': 5,  'descripcion': 'Valparaíso', 'codigo': 'VA'},
            {'id': 13, 'descripcion': 'Metropolitana de Santiago', 'codigo': 'RM'},
            {'id': 6,  'descripcion': 'Libertador General Bernardo O\'Higgins', 'codigo': 'LI'},
            {'id': 7,  'descripcion': 'Maule', 'codigo': 'ML'},
            {'id': 16, 'descripcion': 'Ñuble', 'codigo': 'NB'},
            {'id': 8,  'descripcion': 'Biobío', 'codigo': 'BI'},
            {'id': 9,  'descripcion': 'La Araucanía', 'codigo': 'AR'},
            {'id': 14, 'descripcion': 'Los Ríos', 'codigo': 'LR'},
            {'id': 10, 'descripcion': 'Los Lagos', 'codigo': 'LL'},
            {'id': 11, 'descripcion': 'Aysén del General Carlos Ibáñez del Campo', 'codigo': 'AI'},
            {'id': 12, 'descripcion': 'Magallanes y de la Antártica Chilena', 'codigo': 'MA'}
        ]
        
        for rd in regiones_data:
            if not Region.query.get(rd['id']):
                db.session.add(Region(**rd))
        
        db.session.flush()
        
        # 9. Cargar Comunas desde JSON (346 comunas)
        print("Cargando las 346 comunas de Chile...")
        try:
            path_json = os.path.join(os.path.dirname(__file__), 'app', 'resources', 'comunas_chile.json')
            with open(path_json, 'r', encoding='utf-8') as f:
                comunas_data = json.load(f)
                for cd in comunas_data:
                    if not Comuna.query.filter_by(codigo=cd['codigo']).first():
                        # Usar cd sin el 'id' para que la BD asigne su propio autoincremental si es necesario, 
                        # o mantenerlo si quieres IDs fijos. Aquí mantendremos la lógica de código único.
                        db.session.add(Comuna(
                            codigo=cd['codigo'],
                            descripcion=cd['descripcion'],
                            region_id=cd['region_id']
                        ))
        except Exception as e:
            print(f"Advertencia: No se pudieron cargar las comunas: {e}")

        db.session.commit()
        print("\n--- ¡Inicialización Maestra Exitosa! ---")
        print("Acceso Admin: orozasi@gmail.com / admin123")

if __name__ == '__main__':
    init_db()

from datetime import datetime, timedelta
from app.database import db
from app.models.business import Trabajador, Turno, TrabajadorAusencia, TrabajadorRestriccionTurno
from app.scheduler.builder import build_model
from app.services.config_manager import ConfigManager
from app.services.legal_engine import LegalEngine

class SchedulingService:
    @staticmethod
    def run_generation(mes: int, anio: int, sucursal_id: int):
        """
        Orquesta el proceso completo de generación de cuadrante.
        1. Prepara datos.
        2. Llama al Builder.
        3. Guarda resultados.
        """
        ConfigManager.clear_cache()
        ConfigManager.preload()

        # Rango de fechas
        fecha_inicio = datetime(anio, mes, 1).date()
        if mes == 12:
            fecha_fin = datetime(anio + 1, 1, 1).date() - timedelta(days=1)
        else:
            fecha_fin = datetime(anio, mes + 1, 1).date() - timedelta(days=1)

        dias_del_mes = [(fecha_inicio + timedelta(days=i)).isoformat() 
                        for i in range((fecha_fin - fecha_inicio).days + 1)]

        # 1. Cargar Entidades
        trabajadores = Trabajador.query.filter_by(servicio_id=sucursal_id, activo=True).all()
        turnos = Turno.query.filter_by(servicio_id=sucursal_id, activo=True).all()
        
        if not trabajadores or not turnos:
            return {'status': 'error', 'message': 'No hay trabajadores o turnos activos en esta sucursal.'}

        # 2. Preparar Metadatos
        trabajadores_meta = {w.id: {
            'horas_semanales': w.horas_semanales,
            'tipo_contrato': w.tipo_contrato,
            'permite_horas_extra': w.permite_horas_extra
        } for w in trabajadores}

        turnos_meta = {t.id: {
            'nombre': t.nombre,
            'horas': t.duracion_hrs,
            'es_nocturno': t.es_nocturno,
            'dotacion': t.dotacion_diaria
        } for t in turnos}

        # 3. Cargar Restricciones (Ausencias y Especiales)
        bloqueados = []
        ausencias = TrabajadorAusencia.query.filter(
            TrabajadorAusencia.trabajador_id.in_([w.id for w in trabajadores]),
            TrabajadorAusencia.fecha_inicio <= fecha_fin,
            TrabajadorAusencia.fecha_fin >= fecha_inicio
        ).all()
        for a in ausencias:
            if a.es_bloqueo_dia:
                curr = max(a.fecha_inicio, fecha_inicio)
                while curr <= min(a.fecha_fin, fecha_fin):
                    bloqueados.append((a.trabajador_id, curr.isoformat()))
                    curr += timedelta(days=1)

        restricciones = TrabajadorRestriccionTurno.query.filter(
            TrabajadorRestriccionTurno.trabajador_id.in_([w.id for w in trabajadores]),
            TrabajadorRestriccionTurno.fecha_inicio <= fecha_fin,
            TrabajadorRestriccionTurno.fecha_fin >= fecha_inicio,
            TrabajadorRestriccionTurno.activo == True
        ).all()

        r_hard = []
        r_soft = []
        fijos = {}
        
        for r in restricciones:
            curr = max(r.fecha_inicio, fecha_inicio)
            while curr <= min(r.fecha_fin, fecha_fin):
                if r.dias_semana is None or curr.weekday() in r.dias_semana:
                    if r.tipo == 'turno_fijo':
                        fijos[(r.trabajador_id, curr.isoformat())] = r.turno_id
                    elif r.tipo == 'turno_preferente':
                        r_soft.append({'w': r.trabajador_id, 'd': curr.isoformat(), 't': r.turno_id, 'weight': 500})
                    else:
                        r_hard.append({'w': r.trabajador_id, 'd': curr.isoformat(), 't': r.turno_id, 'action': r.tipo})
                curr += timedelta(days=1)

        # 4. Dotación (Cobertura)
        coberturas = {d: {t.id: t.dotacion_diaria for t in turnos} for d in dias_del_mes}

        # 4b. Pre-validación dominical (INC-04b): Detectar INFEASIBLE silencioso antes del Solver
        alertas_dominicales = SchedulingService.validar_domingos_factibles(
            trabajadores, dias_del_mes, set(bloqueados), coberturas
        )
        if alertas_dominicales:
            alertas_criticas = [a for a in alertas_dominicales if a['nivel'] == 'CRITICO']
            if alertas_criticas:
                return {
                    'status': 'warning',
                    'alertas': alertas_criticas,
                    'message': f'{len(alertas_criticas)} trabajador(es) con HR7 activo no tienen domingos disponibles suficientes. El cuadrante puede ser INFEASIBLE.'
                }

        # 5. Ejecutar Solver
        try:
            model, x = build_model(
                [w.id for w in trabajadores],
                dias_del_mes,
                [t.id for t in turnos],
                coberturas,
                bloqueados,
                fijos,
                restricciones_hard=r_hard,
                restricciones_soft=r_soft,
                trabajadores_meta=trabajadores_meta,
                turnos_meta=turnos_meta
            )
            
            from ortools.sat.python import cp_model
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = ConfigManager.get_int("SOLVER_TIMEOUT_SEG", 60)
            status = solver.Solve(model)

            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                asignaciones = []
                for w in [w.id for w in trabajadores]:
                    for d in dias_del_mes:
                        for t in [t.id for t in turnos]:
                            if solver.Value(x[w, d, t]):
                                asignaciones.append({
                                    'trabajador_id': w,
                                    'fecha': d,
                                    'turno_id': t
                                })
                return {'status': 'success', 'data': asignaciones}
            else:
                return {'status': 'error', 'message': 'No se encontró una solución factible con las reglas actuales.'}

        except Exception as e:
            return {'status': 'error', 'message': f'Error en el motor de resolución: {str(e)}'}

    @staticmethod
    def validar_cobertura_factible(trabajadores, turnos, dias_del_mes, bloqueados) -> list:
        """
        Detecta días donde las ausencias dejan cobertura imposible.
        """
        alertas = []
        # Convertimos bloqueados a set para búsqueda rápida
        bloq_set = set(bloqueados)

        for d_str in dias_del_mes:
            # Trabajadores disponibles este día
            disponibles_dia = [w.id for w in trabajadores if (w.id, d_str) not in bloq_set]
            
            for t in turnos:
                if len(disponibles_dia) < t.dotacion_diaria:
                    alertas.append({
                        "fecha": d_str,
                        "turno": t.nombre,
                        "disponibles": len(disponibles_dia),
                        "requeridos": t.dotacion_diaria,
                        "faltantes": t.dotacion_diaria - len(disponibles_dia)
                    })
        return alertas

    @staticmethod
    def validar_domingos_factibles(trabajadores, dias_del_mes, bloqueados_set, coberturas) -> list:
        """
        [INC-04b] Pre-validación dominical antes del Solver.

        Detecta si algún trabajador afecto a HR7 tiene 0 domingos trabajables
        pero hay demanda dominical. Esto causaría INFEASIBLE silencioso en el Solver.
        """
        from datetime import datetime as _dt
        alertas = []
        min_libres = ConfigManager.get_int('MIN_DOMINGOS_LIBRES_MES', 2)
        domingos_mes = [d for d in dias_del_mes
                        if _dt.strptime(d, '%Y-%m-%d').weekday() == 6]

        if not domingos_mes:
            return []

        hay_demanda_dominical = any(
            sum(coberturas.get(d, {}).values()) > 0
            for d in domingos_mes
        )

        for w in trabajadores:
            if not LegalEngine.aplica_domingo_obligatorio(w):
                continue

            dom_disponibles = [
                d for d in domingos_mes
                if (w.id, d) not in bloqueados_set
            ]
            max_trabajables = max(0, len(dom_disponibles) - min_libres)

            if max_trabajables == 0 and hay_demanda_dominical:
                alertas.append({
                    'nivel': 'CRITICO',
                    'trabajador_id': w.id,
                    'nombre': f'{w.nombre} {w.apellido1}',
                    'mensaje': (
                        f'Solo tiene {len(dom_disponibles)} domingo(s) disponible(s) '
                        f'y debe librar {min_libres}. No puede cubrir ningún domingo. '
                        f'Revisar ausencias o reasignar dotación dominical.'
                    )
                })
            elif len(dom_disponibles) < min_libres:
                alertas.append({
                    'nivel': 'INFO',
                    'trabajador_id': w.id,
                    'nombre': f'{w.nombre} {w.apellido1}',
                    'mensaje': (
                        f'Solo tiene {len(dom_disponibles)} domingo(s) disponible(s), '
                        f'menos que el mínimo legal de {min_libres} domingos libres.'
                    )
                })
        return alertas

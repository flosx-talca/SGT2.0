from datetime import date, timedelta
import calendar as cal_module
from app.models.business import Trabajador, TrabajadorAusencia, Turno, TrabajadorPreferencia

def calcular_capacidad_detallada(empresa_id, mes, anio, ausencias_temporales=None, exclude_ausencia_id=None):
    """
    Calcula disponibilidad vs dotación requerida día por día y turno por turno.
    
    Args:
        empresa_id: ID de la empresa a analizar
        mes: Mes (1-12)
        anio: Año
        ausencias_temporales: Lista de dicts [{'trabajador_id': int, 'fecha_inicio': date, 'fecha_fin': date}]
                             para simular impacto antes de guardar.
        exclude_ausencia_id: ID de ausencia a ignorar (útil en edición).
    """
    if ausencias_temporales is None:
        ausencias_temporales = []

    # 1. Obtener días del mes
    try:
        _, num_dias = cal_module.monthrange(anio, mes)
    except:
        return {'estado': 'error', 'mensaje': 'Fecha inválida', 'dias_con_problema': []}
        
    dias_mes = [date(anio, mes, d) for d in range(1, num_dias + 1)]
    
    # 2. Obtener turnos y su dotación requerida
    turnos = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    if not turnos:
        return {'estado': 'ok', 'mensaje': 'No hay turnos configurados.', 'dias_con_problema': []}
    
    # 3. Obtener trabajadores activos de la empresa
    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).all()
    
    # 4. Mapa de ausencias reales confirmadas en el sistema
    ausencias_reales = TrabajadorAusencia.query.join(Trabajador).filter(Trabajador.empresa_id == empresa_id).all()
    
    # 5. Cálculo por cada día/turno
    dias_con_problema = []
    
    for d in dias_mes:
        d_str = d.strftime('%Y-%m-%d')
        py_weekday = d.weekday() # 0=Mon, 6=Sun
        
        for t in turnos:
            req = t.dotacion_diaria or 0
            if req <= 0: continue
            
            disponibles = 0
            for w in trabajadores:
                # A. ¿Está en ausencia real confirmada?
                en_ausencia = False
                for a in ausencias_reales:
                    if exclude_ausencia_id and a.id == exclude_ausencia_id:
                        continue
                    if a.trabajador_id == w.id and a.fecha_inicio <= d <= a.fecha_fin:
                        en_ausencia = True
                        break
                if en_ausencia: continue
                
                # B. ¿Está en la ausencia temporal que estamos simulando?
                en_temporal = False
                for at in ausencias_temporales:
                    if at['trabajador_id'] == w.id and at['fecha_inicio'] <= d <= at['fecha_fin']:
                        en_temporal = True
                        break
                if en_temporal: continue
                
                # C. ¿Puede hacer este turno basado en sus preferencias permanentes?
                # Si tiene tipo='solo_turno', solo puede hacer esos turnos
                turnos_solo = [p.turno for p in w.preferencias if p.tipo == 'solo_turno']
                if turnos_solo and t.abreviacion not in turnos_solo:
                    continue
                
                # Si tiene tipo='preferencia' para este día de la semana
                prefs_dia = [p.turno for p in w.preferencias if p.dia_semana == py_weekday and p.tipo == 'preferencia']
                if prefs_dia and t.abreviacion not in prefs_dia:
                    continue

                # Si tiene tipo='fijo' para este día de la semana
                fijos_dia = [p.turno for p in w.preferencias if p.dia_semana == py_weekday and p.tipo == 'fijo']
                if fijos_dia and t.abreviacion not in fijos_dia:
                    # Si tiene un fijo en OTRO turno para este día, no está disponible para este turno
                    continue
                
                # TODO: Estimación de domingos libres (HR7)
                # Por ahora, si es domingo, asumimos que todos los trabajadores sin ausencia están disponibles,
                # lo cual es optimista. El solver será más restrictivo.
                
                disponibles += 1
            
            if disponibles < req:
                dias_con_problema.append({
                    'fecha': d.strftime('%d/%m'),
                    'fecha_full': d_str,
                    'dia_semana': ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][py_weekday],
                    'turno': t.abreviacion,
                    'requerido': req,
                    'disponible': disponibles,
                    'deficit': req - disponibles
                })

    if not dias_con_problema:
        return {'estado': 'ok', 'mensaje': 'La dotación del mes se mantiene cubierta.', 'dias_con_problema': []}
    
    total_problemas = len(dias_con_problema)
    return {
        'estado': 'critico' if total_problemas > 0 else 'ok',
        'mensaje': f'{total_problemas} combinaciones día/turno sin cobertura suficiente.',
        'dias_con_problema': dias_con_problema
    }

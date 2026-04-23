from ortools.sat.python import cp_model

def extract_solution(solver, status, x, trabajadores, dias_del_mes, turnos, ausencias):
    """
    Si el solver encontró una solución, extrae las variables asignadas.
    
    Args:
        solver: cp_model.CpSolver
        status: status del solver
        x: dict de variables del modelo
        trabajadores: lista de IDs
        dias_del_mes: lista de fechas str
        turnos: lista de turnos
        ausencias: dict de ausencias {(w, d): motivo}
        
    Returns:
        celdas: Dict { "fecha": { "worker_id": "turno_o_L_o_VAC" } }
    """
    celdas = {}
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for d in dias_del_mes:
            celdas[d] = {}
            for w in trabajadores:
                # Verificamos si tiene ausencia primero
                if (w, d) in ausencias:
                    celdas[d][w] = ausencias[(w, d)] # Ej: 'VAC', 'LM'
                    continue
                
                # Buscar qué turno se le asignó
                turno_asignado = 'L' # Por defecto Libre
                for t in turnos:
                    if solver.Value(x[w, d, t]) == 1:
                        turno_asignado = t
                        break
                
                celdas[d][w] = turno_asignado
    
    return celdas

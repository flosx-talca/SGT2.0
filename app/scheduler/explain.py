from ortools.sat.python import cp_model

def extract_solution(solver, status, x, trabajadores, dias_del_mes, turnos, ausencias):
    """
    Extrae las variables asignadas por el solver y construye el cuadrante.

    Siempre retorna la matriz completa con todos los trabajadores y días,
    independientemente del status del solver. Esto permite que el frontend
    muestre la grilla y el usuario complete manualmente las celdas vacías.

    Valores posibles por celda:
        "T1", "M", "N", etc.  → turno asignado por el solver
        "L"                   → libre (el solver asignó día de descanso)
        "VAC", "LM", etc.     → ausencia (vacaciones, licencia médica, etc.)
        ""                    → sin resolver (INFEASIBLE: el solver no pudo asignar)

    Args:
        solver:        cp_model.CpSolver
        status:        status del solver (OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN)
        x:             dict de variables del modelo { (w, d, t): BoolVar }
        trabajadores:  lista de IDs de trabajadores
        dias_del_mes:  lista de fechas str 'YYYY-MM-DD'
        turnos:        lista de IDs de turno
        ausencias:     dict { (worker_id, fecha): motivo }

    Returns:
        celdas: Dict { "fecha": { worker_id: valor } }
    """
    celdas = {}

    solucion_disponible = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    for d in dias_del_mes:
        celdas[d] = {}
        for w in trabajadores:

            # Ausencias siempre tienen prioridad, independiente del solver
            if (w, d) in ausencias:
                celdas[d][w] = str(ausencias[(w, d)]).strip()
                continue

            if solucion_disponible:
                # Buscar qué turno asignó el solver
                turno_asignado = 'L'    # libre por defecto si no asignó turno
                for t in turnos:
                    if solver.Value(x[w, d, t]) == 1:
                        turno_asignado = t
                        break
                celdas[d][w] = turno_asignado
            else:
                # Sin solución: celda vacía para que el usuario complete manualmente
                # "" es distinto de "L" — L significa libre asignado, "" significa sin resolver
                celdas[d][w] = ''

    return celdas

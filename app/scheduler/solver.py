from ortools.sat.python import cp_model

def solve_model(model):
    """
    Ejecuta el solver de OR-Tools con un límite de tiempo.
    
    Args:
        model: Objeto cp_model.CpModel
    
    Returns:
        solver: Objeto cp_model.CpSolver con el resultado de la ejecución.
        status: status (OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN)
    """
    solver = cp_model.CpSolver()
    
    # Configuramos un límite de tiempo para no colgar la UI
    # Para problemas de cuadrantes mensuales, 30 segundos permiten una optimización mucho más profunda.
    solver.parameters.max_time_in_seconds = 30.0
    
    status = solver.Solve(model)
    return solver, status

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
    # En problemas grandes, 15 segundos es un buen compromiso para retornar la mejor solución factible encontrada.
    solver.parameters.max_time_in_seconds = 15.0
    
    status = solver.Solve(model)
    return solver, status

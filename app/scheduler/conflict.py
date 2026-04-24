from ortools.sat.python import cp_model

def get_conflict_report(status):
    """
    Retorna un reporte de conflicto si el solver falló.
    
    Args:
        status: status del solver
        
    Returns:
        Dict con el error.
    """
    if status == cp_model.INFEASIBLE:
        return {
            "error": True,
            "message": "Es matemáticamente imposible cumplir con todas las coberturas y reglas a la vez con la dotación de personal disponible. Intente reducir las coberturas mínimas o flexibilizar las reglas."
        }
    elif status == cp_model.UNKNOWN:
        return {
            "error": True,
            "message": "El solver agotó el tiempo límite (15s) antes de poder encontrar siquiera una solución viable. El problema podría ser demasiado complejo o estar sobre-restringido."
        }
    return None

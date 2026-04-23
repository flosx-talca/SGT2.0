from ortools.sat.python import cp_model

def build_model(trabajadores, dias_del_mes, turnos, coberturas, ausencias, preferencias):
    """
    Construye el modelo CP-SAT.
    
    Args:
        trabajadores (list): Lista de IDs de trabajadores.
        dias_del_mes (list): Lista de días (ej. ["2025-05-01", "2025-05-02", ...]).
        turnos (list): Lista de tipos de turno (ej. ['M', 'I', 'T', 'N']).
        coberturas (dict): {turno: cantidad_requerida}.
        ausencias (dict): {(worker_id, fecha_str): motivo}.
        preferencias (dict): {(worker_id, fecha_str): turno_str}.
    
    Returns:
        model: Objeto cp_model.CpModel
        x: Diccionario de variables booleanas x[w, d, t]
    """
    model = cp_model.CpModel()
    
    # 1. Variables: x[w, d, t] = 1 si se asigna el turno t al trabajador w en el día d
    x = {}
    for w in trabajadores:
        for d in dias_del_mes:
            for t in turnos:
                x[w, d, t] = model.NewBoolVar(f'x_{w}_{d}_{t}')

    # 2. Hard Rule: Máximo 1 turno por día por trabajador
    for w in trabajadores:
        for d in dias_del_mes:
            model.AddAtMostOne(x[w, d, t] for t in turnos)

    # 3. Hard Rule: Ausencias (Vacaciones, Licencias Médicas, etc.)
    # Si tiene ausencia registrada, bloqueamos la asignación de cualquier turno ese día
    for (w, d), motivo in ausencias.items():
        if w in trabajadores and d in dias_del_mes:
            for t in turnos:
                model.Add(x[w, d, t] == 0)

    # 4. Hard Rule: Preferencias específicas (Turnos fijos pre-asignados en mantenedor)
    # Estos son los primeros en anclarse (forced = 1)
    for (w, d), pref_t in preferencias.items():
        if w in trabajadores and d in dias_del_mes and pref_t in turnos:
            model.Add(x[w, d, pref_t] == 1)

    # 5. Hard Rule: Cobertura mínima por turno
    # Garantizar que sum(x) >= cobertura requerida diaria
    for d in dias_del_mes:
        for t in turnos:
            req = coberturas.get(t, 0)
            model.Add(sum(x[w, d, t] for w in trabajadores) >= req)

    # 6. Hard Rule: Límite de días consecutivos (Máximo 6 días de trabajo a la semana)
    # Por cada ventana móvil de 7 días, un trabajador puede trabajar como máximo 6 días
    for w in trabajadores:
        for i in range(len(dias_del_mes) - 6):
            ventana_7_dias = dias_del_mes[i:i+7]
            model.Add(sum(x[w, d, t] for d in ventana_7_dias for t in turnos) <= 6)

    # 7. Soft Rule: Penalizar fragmentación (Ej. trabajar 1 día suelto)
    # Se penaliza si un trabajador tiene un turno hoy, pero mañana tiene libre.
    # En la práctica esto incentiva a agrupar los turnos.
    penalizaciones = []
    for w in trabajadores:
        for i in range(len(dias_del_mes) - 1):
            d_hoy = dias_del_mes[i]
            d_manana = dias_del_mes[i+1]
            
            trabaja_hoy = model.NewBoolVar(f'trab_hoy_{w}_{d_hoy}')
            trabaja_manana = model.NewBoolVar(f'trab_man_{w}_{d_manana}')
            
            # Link bool vars
            model.Add(trabaja_hoy == sum(x[w, d_hoy, t] for t in turnos))
            model.Add(trabaja_manana == sum(x[w, d_manana, t] for t in turnos))
            
            # Penalizar (trabaja hoy AND NO trabaja mañana)
            penalty = model.NewBoolVar(f'pen_{w}_{d_hoy}')
            model.AddBoolAnd([trabaja_hoy, trabaja_manana.Not()]).OnlyEnforceIf(penalty)
            # También la inversa: no trabaja hoy y sí mañana
            # model.AddBoolAnd([trabaja_hoy.Not(), trabaja_manana]).OnlyEnforceIf(penalty)
            
            penalizaciones.append(penalty)

    # Minimizar las penalizaciones para lograr un calendario más estable
    model.Minimize(sum(penalizaciones))

    return model, x

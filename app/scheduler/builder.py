from ortools.sat.python import cp_model
import calendar as cal_module

def build_model(trabajadores, dias_del_mes, turnos, coberturas, ausencias, preferencias,
                reglas=None, trabajadores_meta=None):
    """
    Construye el modelo CP-SAT con todas las reglas del cliente.

    Reglas implementadas:
      HARD-1: Máximo 1 turno por día por trabajador.
      HARD-2: Ausencias bloquean cualquier asignación (Licencias, Vacaciones).
      HARD-3: Ley 6x2: Máximo 6 días trabajados en cualquier ventana de 8 días.
      HARD-4: Ley Domingos: Mínimo 2 domingos libres al mes.
      
      P1 (peso 1.000.000): Cobertura de dotación (evitar Déficit).
      P2 (peso 10.000):    Dotación exacta por turno (evitar Exceso).
      P3 (peso 10.000):    Respetar preferencias del trabajador (Soft Rule).
      P4 (peso 1.000):     Máximo días semanales (Diferenciado por Contrato/Horas).
      P5 (peso 500):       Mínimo días semanales (Diferenciado por Contrato/Horas).
      P6 (peso 10):        Penalizar fragmentación (turnos aislados).
      P7 (recompensa):     Utilización de personal disponible.

    Args:
        trabajadores (list):      Lista de IDs de trabajadores.
        dias_del_mes (list):      Lista de strings 'YYYY-MM-DD'.
        turnos (list):            Lista de abreviaciones de turnos.
        coberturas (dict):        Dict { 'fecha': { 'turno': req } } o { 'turno': req } (si es global).
        ausencias (dict):         Dict { (worker_id, fecha): motivo }.
        preferencias (dict):      Dict { (worker_id, fecha): turno }.
        reglas (dict):            Parámetros leídos de ReglaEmpresa en BD.
        trabajadores_meta (dict): {worker_id: {'tipo_contrato': ..., 'horas_semanales': ...}}
    """
    model = cp_model.CpModel()

    # ── Parámetros de reglas (con defaults del Código del Trabajo Chile) ─────────
    if reglas is None:
        reglas = {}
    if trabajadores_meta is None:
        trabajadores_meta = {}

    max_dias_semana  = reglas.get('working_days_limit_max', 6)
    min_dias_semana  = reglas.get('working_days_limit_min', 5)
    min_domingos_lib = reglas.get('min_free_sundays', 2)

    # Identificar domingos del mes (Python weekday: 6 = Domingo)
    domingos = {
        d for d in dias_del_mes
        if cal_module.weekday(int(d[:4]), int(d[5:7]), int(d[8:10])) == 6
    }

    N = len(dias_del_mes)

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-1: Variables booleanas x[w, d, t]
    # ═══════════════════════════════════════════════════════════════════════════
    x = {}
    for w in trabajadores:
        for d in dias_del_mes:
            for t in turnos:
                x[w, d, t] = model.NewBoolVar(f'x_{w}_{d}_{t}')

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-2: Máximo 1 turno por día por trabajador
    # ═══════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        for d in dias_del_mes:
            model.AddAtMostOne(x[w, d, t] for t in turnos)

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-3: Ausencias → ningún turno ese día
    # ═══════════════════════════════════════════════════════════════════════════
    for (w, d), _ in ausencias.items():
        if w in trabajadores and d in dias_del_mes:
            for t in turnos:
                model.Add(x[w, d, t] == 0)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-4 (P=5000): Preferencias de turno del mantenedor
    # Se convierte a SOFT para evitar INFEASIBLE si choca con ausencias o la regla 6-2.
    # ═══════════════════════════════════════════════════════════════════════════
    pref_violadas = []
    for (w, d), pref_t in preferencias.items():
        if w in trabajadores and d in dias_del_mes and pref_t in turnos:
            # Si no se cumple la preferencia, penalizamos
            violation = model.NewBoolVar(f'pref_viol_{w}_{d}')
            model.Add(x[w, d, pref_t] == 1).OnlyEnforceIf(violation.Not())
            model.Add(x[w, d, pref_t] == 0).OnlyEnforceIf(violation)
            pref_violadas.append(violation)

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-5: 6 días consecutivos → 2 días libres obligatorios
    #
    # Equivalencia matemática:
    #   "Tras 6 días seguidos, 2 libres" ≡ "En cualquier ventana de 8 días, ≤ 6 trabajados"
    # Proof: Si en una ventana de 8 días se trabajaran 7+, habría 7 consecutivos,
    # lo que implica que no se tomaron 2 libres tras los primeros 6. Contradicción.
    # ═══════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        for i in range(N - 7):  # ventanas de 8 días: [i, i+7]
            ventana_8 = dias_del_mes[i:i+8]
            model.Add(
                sum(x[w, d, t] for d in ventana_8 for t in turnos) <= 6
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-6: Mínimo de domingos libres al mes (Ley)
    # ═══════════════════════════════════════════════════════════════════════════
    if domingos:
        total_dom = len(domingos)
        max_dom_trabajo = max(0, total_dom - min_domingos_lib)
        for w in trabajadores:
            model.Add(
                sum(x[w, d, t] for d in domingos for t in turnos) <= max_dom_trabajo
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-6: Cobertura por turno (Déficit y Exceso)
    # P1: Evitar déficit (1.000.000)
    # P2: Evitar exceso (10.000) -> Para respetar la dotación exacta por turno.
    # ═══════════════════════════════════════════════════════════════════════════
    deficits = []
    excesses = []
    for d in dias_del_mes:
        # Soporte para coberturas por día o globales
        cob_hoy = coberturas.get(d, coberturas) 
        
        for t in turnos:
            req = cob_hoy.get(t, 0)
            if req > 0:
                assigned = sum(x[w, d, t] for w in trabajadores)
                
                # Déficit (Faltan personas)
                deficit = model.NewIntVar(0, req, f'def_{d}_{t}')
                model.Add(assigned + deficit >= req)
                deficits.append(deficit)

                # Exceso (Sobran personas)
                excess = model.NewIntVar(0, len(trabajadores), f'exc_{d}_{t}')
                model.Add(assigned - excess <= req)
                excesses.append(excess)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-8 (P=1000): Máximo de días trabajados por semana (ventana 7 días)
    # ═══════════════════════════════════════════════════════════════════════════
    dias_extra_max = []
    for w in trabajadores:
        # Ajustar límite según contrato individual
        meta = trabajadores_meta.get(w, {})
        tipo = meta.get('tipo_contrato', 'full-time').lower()
        horas = meta.get('horas_semanales', 45) or 45
        
        # Lógica de tope semanal:
        # Full-time: max 5 o 6 días (según regla empresa)
        # Part-time (30h o menos): max 4 días
        # Muy Part-time (20h o menos): max 2-3 días
        limite_w = max_dias_semana
        if 'part' in tipo or horas <= 30:
            limite_w = 4
        if horas <= 20:
            limite_w = 3

        for i in range(N - 6):
            ventana_7 = dias_del_mes[i:i+7]
            trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
            extra = model.NewIntVar(0, 7, f'extra_max_{w}_{i}')
            model.Add(trabajados - limite_w <= extra)
            dias_extra_max.append(extra)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-9 (P=200): Mínimo de días trabajados por semana (ventana 7 días)
    # No penalizar si la ventana tiene ausencias que justifiquen los libres.
    # ═══════════════════════════════════════════════════════════════════════════
    dias_bajo_min = []
    for w in trabajadores:
        # Ajustar mínimo según contrato individual
        meta = trabajadores_meta.get(w, {})
        tipo = meta.get('tipo_contrato', 'full-time').lower()
        horas = meta.get('horas_semanales', 45) or 45
        
        min_w = min_dias_semana
        if 'part' in tipo or horas <= 30:
            min_w = 2 # Un part-time no suele tener un "mínimo" alto
        if horas <= 20:
            min_w = 1

        for i in range(N - 6):
            ventana_7 = dias_del_mes[i:i+7]
            ausencias_en_ventana = sum(1 for d in ventana_7 if (w, d) in ausencias)
            dias_disponibles = 7 - ausencias_en_ventana
            
            if dias_disponibles >= min_w:
                trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
                faltante = model.NewIntVar(0, min_w, f'bajo_min_{w}_{i}')
                model.Add(trabajados + faltante >= min_w)
                dias_bajo_min.append(faltante)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-10 (P=1): Penalizar fragmentación (trabajar 1 día suelto)
    # ═══════════════════════════════════════════════════════════════════════════
    penalizaciones = []
    for w in trabajadores:
        for i in range(N - 1):
            d_hoy    = dias_del_mes[i]
            d_manana = dias_del_mes[i+1]
            th = model.NewBoolVar(f'th_{w}_{i}')
            tm = model.NewBoolVar(f'tm_{w}_{i}')
            model.Add(th == sum(x[w, d_hoy,    t] for t in turnos))
            model.Add(tm == sum(x[w, d_manana, t] for t in turnos))
            pen = model.NewBoolVar(f'pen_{w}_{i}')
            model.AddBoolAnd([th, tm.Not()]).OnlyEnforceIf(pen)
            penalizaciones.append(pen)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-11 (P=100.000): Equidad de Carga (Load Balancing)
    # Minimizamos la DIFERENCIA entre el que más trabaja y el que menos.
    # Esto obliga a que todos se acerquen al mismo promedio.
    # ═══════════════════════════════════════════════════════════════════════════
    max_total_trabajado = model.NewIntVar(0, N, 'max_total_trabajado')
    min_total_trabajado = model.NewIntVar(0, N, 'min_total_trabajado')
    for w in trabajadores:
        total_w = sum(x[w, d, t] for d in dias_del_mes for t in turnos)
        model.Add(total_w <= max_total_trabajado)
        model.Add(total_w >= min_total_trabajado)
    
    # El "spread" o rango de carga
    rango_carga = model.NewIntVar(0, N, 'rango_carga')
    model.Add(rango_carga == max_total_trabajado - min_total_trabajado)

    # ═══════════════════════════════════════════════════════════════════════════
    # Función objetivo multi-criterio
    # ═══════════════════════════════════════════════════════════════════════════
    # P1: Cobertura (Prioridad Absoluta)
    obj_deficit  = sum(deficits)         * 10000000 if deficits else 0
    obj_excess   = sum(excesses)         * 100000   if excesses else 0
    # P2: Equidad y Preferencias
    obj_equidad  = rango_carga           * 100000 
    obj_pref     = sum(pref_violadas)    * 10000    if pref_violadas else 0
    # P3: Reglas de descanso y carga
    obj_max_sem  = sum(dias_extra_max)   * 1000     if dias_extra_max else 0
    obj_min_sem  = sum(dias_bajo_min)    * 2000     if dias_bajo_min else 0
    obj_frag     = sum(penalizaciones)   * 10       if penalizaciones else 0

    # P4: Utilización (Solo si no perjudica a las anteriores)
    # Recompensamos asignaciones, pero solo si hay un requerimiento ese día para ese turno.
    reward_list = []
    for d in dias_del_mes:
        cob_hoy = coberturas.get(d, coberturas)
        for t in turnos:
            if cob_hoy.get(t, 0) > 0:
                for w in trabajadores:
                    reward_list.append(x[w, d, t])

    reward = sum(reward_list)

    model.Minimize(
        obj_deficit + obj_excess + obj_pref + obj_max_sem + obj_min_sem + obj_equidad + obj_frag
        - reward * 1
    )

    return model, x

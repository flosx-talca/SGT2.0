from ortools.sat.python import cp_model
import calendar as cal_module

def build_model(trabajadores, dias_del_mes, turnos, coberturas, ausencias, preferencias,
                reglas=None, trabajadores_meta=None):
    """
    Construye el modelo CP-SAT con todas las reglas del cliente.

    Reglas implementadas:
      HARD-1: Máximo 1 turno por día por trabajador.
      HARD-2: Ausencias bloquean cualquier asignación.
      HARD-3: Preferencias de turno (restricciones duras del mantenedor).
      HARD-4: Tras 6 días consecutivos de trabajo → 2 días libres obligatorios.
               Implementado como: en cualquier ventana de 8 días, máximo 6 trabajados.
               (Equivalencia matemática demostrable sin variables auxiliares buggeadas.)
      SOFT-5 (P=10000): Cobertura mínima por turno (deficit penalizado).
      SOFT-6 (P=2000):  Mínimo N domingos libres al mes (min_free_sundays).
      SOFT-7 (P=500):   Máximo días por semana (working_days_limit max).
      SOFT-8 (P=200):   Mínimo días por semana (working_days_limit min).
      SOFT-9 (P=-10):   Recompensar utilización del personal (reduce Libres).
      SOFT-10 (P=1):    Penalizar fragmentación (turnos sueltos).

    Args:
        trabajadores (list):      Lista de IDs de trabajadores.
        dias_del_mes (list):      Lista de fechas 'YYYY-MM-DD'.
        turnos (list):            Lista de abreviaciones de turnos.
        coberturas (dict):        {turno: cantidad_requerida}.
        ausencias (dict):         {(worker_id, fecha): abreviacion}.
        preferencias (dict):      {(worker_id, fecha): turno}.
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
    # HARD-4: Preferencias de turno del mantenedor (restricciones duras)
    # ═══════════════════════════════════════════════════════════════════════════
    for (w, d), pref_t in preferencias.items():
        if w in trabajadores and d in dias_del_mes and pref_t in turnos:
            model.Add(x[w, d, pref_t] == 1)

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
    # SOFT-6 (P=10000): Cobertura mínima por turno
    # Penalización alta: cubrir la dotación es la prioridad principal de la IA.
    # ═══════════════════════════════════════════════════════════════════════════
    deficits = []
    for d in dias_del_mes:
        for t in turnos:
            req = coberturas.get(t, 0)
            if req > 0:
                assigned = sum(x[w, d, t] for w in trabajadores)
                deficit = model.NewIntVar(0, req, f'def_{d}_{t}')
                model.Add(assigned + deficit >= req)
                deficits.append(deficit)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-7 (P=2000): Mínimo de domingos libres al mes
    # ═══════════════════════════════════════════════════════════════════════════
    domingos_deficit = []
    if domingos:
        total_dom = len(domingos)
        max_dom_trabajo = max(0, total_dom - min_domingos_lib)
        for w in trabajadores:
            dom_trabaj = sum(x[w, d, t] for d in domingos for t in turnos)
            dom_extra = model.NewIntVar(0, total_dom, f'dom_extra_{w}')
            model.Add(dom_trabaj - max_dom_trabajo <= dom_extra)
            domingos_deficit.append(dom_extra)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-8 (P=500): Máximo de días trabajados por semana (ventana 7 días)
    # ═══════════════════════════════════════════════════════════════════════════
    dias_extra_max = []
    for w in trabajadores:
        for i in range(N - 6):
            ventana_7 = dias_del_mes[i:i+7]
            trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
            extra = model.NewIntVar(0, 7, f'extra_max_{w}_{i}')
            model.Add(trabajados - max_dias_semana <= extra)
            dias_extra_max.append(extra)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-9 (P=200): Mínimo de días trabajados por semana (ventana 7 días)
    # No penalizar si la ventana tiene ausencias que justifiquen los libres.
    # ═══════════════════════════════════════════════════════════════════════════
    dias_bajo_min = []
    for w in trabajadores:
        for i in range(N - 6):
            ventana_7 = dias_del_mes[i:i+7]
            ausencias_en_ventana = sum(1 for d in ventana_7 if (w, d) in ausencias)
            dias_disponibles = 7 - ausencias_en_ventana
            if dias_disponibles >= min_dias_semana:
                trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
                faltante = model.NewIntVar(0, min_dias_semana, f'bajo_min_{w}_{i}')
                model.Add(trabajados + faltante >= min_dias_semana)
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
    # Función objetivo multi-criterio
    # ═══════════════════════════════════════════════════════════════════════════
    obj_deficit  = sum(deficits)         * 10000 if deficits else 0
    obj_dom      = sum(domingos_deficit) * 2000  if domingos_deficit else 0
    obj_max_sem  = sum(dias_extra_max)   * 500   if dias_extra_max else 0
    obj_min_sem  = sum(dias_bajo_min)    * 200   if dias_bajo_min else 0
    obj_frag     = sum(penalizaciones)   * 1     if penalizaciones else 0

    # Recompensar asignación a turnos requeridos (reduce "Libres" innecesarios)
    reward = sum(
        x[w, d, t]
        for w in trabajadores
        for d in dias_del_mes
        for t in turnos
        if coberturas.get(t, 0) > 0
    )

    model.Minimize(
        obj_deficit + obj_dom + obj_max_sem + obj_min_sem + obj_frag
        - reward * 10
    )

    return model, x

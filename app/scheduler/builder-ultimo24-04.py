from ortools.sat.python import cp_model
import calendar as cal_module
import math
from collections import defaultdict

# ── Pesos de la función objetivo ─────────────────────────────────────────────
# Ajustar aquí para calibrar sin tocar la lógica del modelo.
# La separación de órdenes de magnitud garantiza la jerarquía de prioridades:
# resolver 1 déficit siempre vale más que resolver cualquier cantidad de reglas menores.
W_DEFICIT  = 10_000_000
W_EXCESO   =    100_000
W_EQUIDAD  =    100_000
W_MIN_SEM  =      2_000
W_MAX_SEM  =      1_000
W_FRAG     =        100
W_REWARD   =          1
W_ASIG     =  1_000_000   # asignaciones fijas por día de semana (muy alto, cede solo ante HARD)
W_CONSEC   =         50   # reward por días consecutivos trabajados (agrupa libres, ayuda al part-time)
W_EQ_SEM   =      5_000   # equidad de carga semanal por grupo de contrato


def build_model(trabajadores, dias_del_mes, turnos, coberturas, ausencias,
                asignaciones_fijas, reglas=None, trabajadores_meta=None,
                turnos_meta=None):
    """
    Construye el modelo CP-SAT con todas las reglas del cliente.

    Reglas HARD (siempre activas, violarlas hace el problema INFEASIBLE):
      HARD-1: Máximo 1 turno por día por trabajador.
      HARD-2: Ausencias bloquean cualquier asignación.
      HARD-3: Asignaciones fijas por día de semana (turno obligatorio por labor).
      HARD-4: Ley descanso configurable: máx 6 días en ventana (6 + dias_descanso_post_6).
      HARD-5: Mínimo domingos libres al mes (configurable por cliente).
      HARD-6: Post turno nocturno → solo puede trabajar otro turno nocturno al día siguiente.
      HARD-7: Total mensual de turnos según contrato del trabajador.

    Reglas SOFT (función objetivo multi-criterio):
      P1 (× 10.000.000): Cobertura — evitar déficit de personal en un turno.
      P2 (×    100.000): Exceso de cobertura + Equidad de carga por grupo de contrato.
      P3 (×      2.000): Mínimo días semanales por contrato.
      P4 (×      1.000): Máximo días semanales por contrato.
      P5 (×        100): Anti-fragmentación (día trabajado aislado entre dos libres).
      R  (×          1): Reward — utilización del personal cuando hay cobertura requerida.

    Args:
        trabajadores (list):         Lista de IDs de trabajadores.
        dias_del_mes (list):         Lista de strings 'YYYY-MM-DD'.
        turnos (list):               Lista de IDs de turno.
        coberturas (dict):           { turno: req } global o { fecha: { turno: req } } por día.
        ausencias (dict):            { (worker_id, fecha): motivo }.
        asignaciones_fijas (dict):   { (worker_id, fecha): turno_id } → HARD obligatorio.
                                     Antes llamado 'preferencias', ahora es restricción dura
                                     porque refleja la labor específica del trabajador.
        reglas (dict):               Parámetros del cliente leídos desde BD:
                                       working_days_limit_max  (default 6)
                                       working_days_limit_min  (default 5)
                                       min_free_sundays        (default 2)
                                       dias_descanso_post_6    (default 1, ley mínima)
                                       duracion_turno          (default 8)
                                       jornada_semanal         (default 42)
        trabajadores_meta (dict):    { worker_id: { horas_semanales, duracion_turno } }.
                                     No se usa tipo_contrato. El builder trabaja solo con
                                     horas. Si el resultado horas/duracion no es entero,
                                     se aplica ceil y el empleador asume el turno extra.
        turnos_meta (dict):          { turno_id: { es_nocturno, horas } }.
                                     Si no se envía, todos los turnos se tratan como diurnos.

    Returns:
        model: cp_model.CpModel con todas las restricciones aplicadas.
        x:     Dict { (worker_id, fecha, turno_id): BoolVar }.

    Nota de compatibilidad:
        El parámetro 'preferencias' fue renombrado a 'asignaciones_fijas' y
        promovido de SOFT a HARD. Actualizar todos los llamadores.
    """

    # ── Validaciones de entrada ───────────────────────────────────────────────
    if not trabajadores:
        raise ValueError("build_model: lista de trabajadores vacía")
    if not turnos:
        raise ValueError("build_model: lista de turnos vacía")
    if not dias_del_mes:
        raise ValueError("build_model: lista de días vacía")

    model = cp_model.CpModel()

    # ── Defaults y parámetros desde reglas del cliente ───────────────────────
    if reglas is None:
        reglas = {}
    if trabajadores_meta is None:
        trabajadores_meta = {}
    if turnos_meta is None:
        turnos_meta = {}

    max_dias_semana  = reglas.get('working_days_limit_max', 6)
    min_dias_semana  = reglas.get('working_days_limit_min', 5)
    min_domingos_lib = reglas.get('min_free_sundays', 2)
    dias_descanso    = reglas.get('dias_descanso_post_6', 1)   # ley mínima = 1, cliente puede pedir más
    duracion_default = reglas.get('duracion_turno', 8)
    jornada_default  = reglas.get('jornada_semanal', 42)

    # ── Clasificar turnos según atributos (no hardcodeado) ───────────────────
    # Si no viene turnos_meta, todos se tratan como diurnos y HARD-6 no aplica.
    turnos_nocturnos = [
        t for t in turnos
        if turnos_meta.get(t, {}).get('es_nocturno', False)
    ]
    turnos_diurnos = [
        t for t in turnos
        if not turnos_meta.get(t, {}).get('es_nocturno', False)
    ]

    # ── Normalizar coberturas → siempre { fecha: { turno: req } } ────────────
    # Soporta formato global { turno: req } o por día { fecha: { turno: req } }
    primera = next(iter(coberturas.values()), None)
    if isinstance(primera, dict):
        coberturas_norm = {d: coberturas.get(d, {}) for d in dias_del_mes}
    else:
        coberturas_norm = {d: coberturas for d in dias_del_mes}

    # ── Identificar domingos del mes ──────────────────────────────────────────
    domingos = {
        d for d in dias_del_mes
        if cal_module.weekday(int(d[:4]), int(d[5:7]), int(d[8:10])) == 6
    }

    N = len(dias_del_mes)

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-1: Variables booleanas x[w, d, t]
    # Una variable por cada combinación trabajador × día × turno.
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
    # Cubre licencias médicas, vacaciones y cualquier otro tipo de ausencia.
    # ═══════════════════════════════════════════════════════════════════════════
    for (w, d), _ in ausencias.items():
        if w in trabajadores and d in dias_del_mes:
            for t in turnos:
                model.Add(x[w, d, t] == 0)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-ASIG (P = W_ASIG): Asignaciones fijas por día de semana
    # Define qué turno debe hacer el trabajador en días específicos.
    # Es SOFT (no HARD) porque puede entrar en conflicto con:
    #   - HARD-8: el total mensual del contrato (ej. 30h no puede trabajar 5 días/sem)
    #   - HARD-6: domingos libres obligatorios
    # El peso W_ASIG = 1.000.000 es muy alto: el solver lo respeta siempre
    # que no viole restricciones legales o contractuales.
    # ═══════════════════════════════════════════════════════════════════════════
    asig_violadas = []
    for (w, d), t_fijo in asignaciones_fijas.items():
        if w in trabajadores and d in dias_del_mes and t_fijo in turnos:
            if (w, d) not in ausencias:
                violation = model.NewBoolVar(f'asig_viol_{w}_{d}')
                model.Add(x[w, d, t_fijo] == 1).OnlyEnforceIf(violation.Not())
                model.Add(x[w, d, t_fijo] == 0).OnlyEnforceIf(violation)
                asig_violadas.append(violation)

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-5: Ley descanso configurable por cliente
    # "Tras 6 días trabajados → dias_descanso días libres"
    # Equivalencia: en ventana de (6 + dias_descanso) días, máx 6 trabajados.
    # Ley mínima Chile: 1 día libre → ventana 7 días.
    # Cliente puede pedir más: 2 días → ventana 8, 4 días → ventana 10, etc.
    # ═══════════════════════════════════════════════════════════════════════════
    ventana_descanso = 6 + dias_descanso
    for w in trabajadores:
        for i in range(N - ventana_descanso + 1):
            dias_ventana = dias_del_mes[i:i + ventana_descanso]
            model.Add(
                sum(x[w, d, t] for d in dias_ventana for t in turnos) <= 6
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-6: Mínimo domingos libres al mes (configurable por cliente)
    # ═══════════════════════════════════════════════════════════════════════════
    if domingos:
        max_dom_trabajo = max(0, len(domingos) - min_domingos_lib)
        for w in trabajadores:
            model.Add(
                sum(x[w, d, t] for d in domingos for t in turnos) <= max_dom_trabajo
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-7: Post turno nocturno → solo puede trabajar otro turno nocturno
    # El trabajador descansa el día completo pero puede entrar a las 23:00.
    # Si no hay turnos_meta definido, esta regla no aplica.
    # ═══════════════════════════════════════════════════════════════════════════
    if turnos_nocturnos and turnos_diurnos:
        for w in trabajadores:
            for i in range(N - 1):
                d_hoy    = dias_del_mes[i]
                d_manana = dias_del_mes[i + 1]
                for t_noc in turnos_nocturnos:
                    model.Add(
                        sum(x[w, d_manana, t] for t in turnos_diurnos) == 0
                    ).OnlyEnforceIf(x[w, d_hoy, t_noc])

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-8: Total mensual de turnos según horas contratadas
    # Resuelve el problema de cuadrantes con exceso de semanas 5×2.
    # El solver ya no puede elegir siempre el mínimo porque el total no cierra.
    #
    # Siempre se usa math.ceil: si horas/duracion no es entero (ej. 42/8=5.25),
    # el turno fraccionario se redondea hacia arriba y el empleador asume ese
    # turno extra. No se distingue entre full-time y part-time: solo importan
    # las horas contratadas.
    #
    # Ejemplos mes 31 días:
    #   32h / 8h = 4.0  → ceil(31/7 × 4.0) = ceil(17.71) = 18 turnos
    #   40h / 8h = 5.0  → ceil(31/7 × 5.0) = ceil(22.14) = 23 turnos
    #   42h / 8h = 5.25 → ceil(31/7 × 5.25) = ceil(23.25) = 24 turnos
    #   44h / 8h = 5.5  → ceil(31/7 × 5.5)  = ceil(24.36) = 25 turnos
    # ═══════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        meta_w   = trabajadores_meta.get(w, {})
        horas    = meta_w.get('horas_semanales', jornada_default) or jornada_default
        duracion = meta_w.get('duracion_turno',  duracion_default) or duracion_default

        ausencias_w      = sum(1 for d in dias_del_mes if (w, d) in ausencias)
        dias_disponibles = N - ausencias_w

        turnos_por_semana = horas / duracion
        meta_mensual      = math.ceil(dias_disponibles / 7 * turnos_por_semana)

        if meta_mensual <= 0:
            continue

        total_w = sum(x[w, d, t] for d in dias_del_mes for t in turnos)

        # Rango ±1 para evitar INFEASIBLE cuando otras reglas HARD
        # (domingos libres, ventana descanso, asignaciones fijas) reducen
        # los días disponibles reales por debajo de la meta exacta.
        meta_min = max(0, meta_mensual - 1)
        meta_max = min(dias_disponibles, meta_mensual + 1)
        model.Add(total_w >= meta_min)
        model.Add(total_w <= meta_max)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-P1/P2: Cobertura por turno (Déficit y Exceso)
    # Usa coberturas normalizadas para evitar el bug del fallback frágil.
    # ═══════════════════════════════════════════════════════════════════════════
    deficits = []
    excesses = []
    for d in dias_del_mes:
        cob_hoy = coberturas_norm[d]
        for t in turnos:
            req = cob_hoy.get(t, 0)
            if req > 0:
                assigned = sum(x[w, d, t] for w in trabajadores)

                deficit = model.NewIntVar(0, req, f'def_{d}_{t}')
                model.Add(assigned + deficit >= req)
                deficits.append(deficit)

                excess = model.NewIntVar(0, len(trabajadores), f'exc_{d}_{t}')
                model.Add(assigned - excess <= req)
                excesses.append(excess)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-P3: Mínimo días semanales por contrato (ventana 7 días)
    # Calculado desde horas_semanales / duracion_turno, no hardcodeado.
    # No penalizar si la ventana tiene ausencias que justifiquen los libres.
    # ═══════════════════════════════════════════════════════════════════════════
    dias_bajo_min = []
    for w in trabajadores:
        meta_w   = trabajadores_meta.get(w, {})
        horas    = meta_w.get('horas_semanales', jornada_default) or jornada_default
        duracion = meta_w.get('duracion_turno',  duracion_default) or duracion_default

        min_w = math.floor(horas / duracion)

        for i in range(N - 6):
            ventana_7        = dias_del_mes[i:i + 7]
            ausencias_v      = sum(1 for d in ventana_7 if (w, d) in ausencias)
            dias_disponibles = 7 - ausencias_v

            if dias_disponibles >= min_w:
                trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
                faltante   = model.NewIntVar(0, min_w, f'bajo_min_{w}_{i}')
                model.Add(trabajados + faltante >= min_w)
                dias_bajo_min.append(faltante)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-P4: Máximo días semanales por contrato (ventana 7 días)
    # Calculado desde horas_semanales / duracion_turno, no hardcodeado.
    # Fix BUG-3: antes usaba umbrales mágicos (horas <= 30, horas <= 20).
    # ═══════════════════════════════════════════════════════════════════════════
    dias_extra_max = []
    for w in trabajadores:
        meta_w   = trabajadores_meta.get(w, {})
        horas    = meta_w.get('horas_semanales', jornada_default) or jornada_default
        duracion = meta_w.get('duracion_turno',  duracion_default) or duracion_default

        # Respetar también el tope global de la empresa
        limite_w = min(math.ceil(horas / duracion), max_dias_semana)

        for i in range(N - 6):
            ventana_7  = dias_del_mes[i:i + 7]
            trabajados = sum(x[w, d, t] for d in ventana_7 for t in turnos)
            extra      = model.NewIntVar(0, 7, f'extra_max_{w}_{i}')
            model.Add(trabajados - limite_w <= extra)
            dias_extra_max.append(extra)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-P5: Anti-fragmentación — penaliza día trabajado aislado
    # Día aislado = ayer libre AND hoy trabajado AND mañana libre.
    # Fix BUG-1: restricción bidireccional para que pen realmente se active.
    # Fix BUG-2: antes penalizaba cualquier transición trabajo→libre (fin de bloque).
    # ═══════════════════════════════════════════════════════════════════════════
    penalizaciones = []
    for w in trabajadores:
        for i in range(1, N - 1):
            d_ayer   = dias_del_mes[i - 1]
            d_hoy    = dias_del_mes[i]
            d_manana = dias_del_mes[i + 1]

            ta = model.NewBoolVar(f'ta_{w}_{i}')
            th = model.NewBoolVar(f'th_{w}_{i}')
            tm = model.NewBoolVar(f'tm_{w}_{i}')

            model.Add(ta == sum(x[w, d_ayer,   t] for t in turnos))
            model.Add(th == sum(x[w, d_hoy,    t] for t in turnos))
            model.Add(tm == sum(x[w, d_manana, t] for t in turnos))

            pen = model.NewBoolVar(f'pen_{w}_{i}')
            # Bidireccional: pen=1 ↔ (ayer libre AND hoy trabajado AND mañana libre)
            model.AddBoolAnd([ta.Not(), th, tm.Not()]).OnlyEnforceIf(pen)
            model.AddBoolOr([ta, th.Not(), tm]).OnlyEnforceIf(pen.Not())
            penalizaciones.append(pen)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-P6: Equidad de carga agrupada por horas_semanales
    # Fix BUG-4: antes comparaba full-time vs part-time, diferencia siempre ~8 días.
    # Ahora compara solo trabajadores del mismo grupo de horas contratadas.
    # ═══════════════════════════════════════════════════════════════════════════
    grupos = defaultdict(list)
    for w in trabajadores:
        horas = (trabajadores_meta.get(w, {}).get('horas_semanales', jornada_default)
                 or jornada_default)
        grupos[horas].append(w)

    rango_cargas = []
    for horas_grupo, workers_grupo in grupos.items():
        if len(workers_grupo) < 2:
            continue
        max_g = model.NewIntVar(0, N, f'max_carga_{horas_grupo}')
        min_g = model.NewIntVar(0, N, f'min_carga_{horas_grupo}')
        for w in workers_grupo:
            total_w = sum(x[w, d, t] for d in dias_del_mes for t in turnos)
            model.Add(total_w <= max_g)
            model.Add(total_w >= min_g)
        rango_g = model.NewIntVar(0, N, f'rango_{horas_grupo}')
        model.Add(rango_g == max_g - min_g)
        rango_cargas.append(rango_g)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-EQ-SEM: Equidad de carga semanal por grupo de contrato
    # Minimiza la diferencia entre el que más y el que menos trabaja
    # en cada ventana semanal, dentro del mismo grupo de horas.
    # Complementa SOFT-P6 (equidad mensual) controlando la distribución
    # dentro del mes — evita que un trabajador trabaje todo al inicio
    # y otro todo al final.
    # Usa ventanas no solapadas de 7 días desde el día 1.
    # ═══════════════════════════════════════════════════════════════════════════
    rango_cargas_sem = []
    for horas_grupo, workers_grupo in grupos.items():
        if len(workers_grupo) < 2:
            continue
        for i in range(0, N, 7):                    # ventanas no solapadas
            semana = dias_del_mes[i:i + 7]
            if not semana:
                continue
            max_s = model.NewIntVar(0, 7, f'max_sem_{horas_grupo}_{i}')
            min_s = model.NewIntVar(0, 7, f'min_sem_{horas_grupo}_{i}')
            for w in workers_grupo:
                dias_s = sum(x[w, d, t] for d in semana for t in turnos)
                model.Add(dias_s <= max_s)
                model.Add(dias_s >= min_s)
            rango_s = model.NewIntVar(0, 7, f'rango_sem_{horas_grupo}_{i}')
            model.Add(rango_s == max_s - min_s)
            rango_cargas_sem.append(rango_s)

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFT-CONSEC: Reward por días trabajados consecutivos
    # Premia cada par de días adyacentes trabajados.
    # Efecto: el solver agrupa los días libres en bloques en vez de
    # dispersarlos, lo que mejora especialmente a los trabajadores part-time
    # que tienen más días libres para distribuir.
    # El reward compite con HARD-5 (máx 6 consecutivos) y HARD-8 (total mensual).
    # ═══════════════════════════════════════════════════════════════════════════
    reward_consec = []
    for w in trabajadores:
        for i in range(N - 1):
            d_hoy    = dias_del_mes[i]
            d_manana = dias_del_mes[i + 1]

            th  = model.NewBoolVar(f'cth_{w}_{i}')
            tm  = model.NewBoolVar(f'ctm_{w}_{i}')
            par = model.NewBoolVar(f'par_{w}_{i}')

            model.Add(th == sum(x[w, d_hoy,    t] for t in turnos))
            model.Add(tm == sum(x[w, d_manana, t] for t in turnos))

            # par = 1 si trabajó hoy Y mañana
            model.AddBoolAnd([th, tm]).OnlyEnforceIf(par)
            model.AddBoolOr([th.Not(), tm.Not()]).OnlyEnforceIf(par.Not())
            reward_consec.append(par)

    # ═══════════════════════════════════════════════════════════════════════════
    # Función objetivo multi-criterio
    # Los pesos están definidos como constantes al inicio del archivo.
    # Para calibrar el comportamiento del solver, ajustar solo esas constantes.
    # ═══════════════════════════════════════════════════════════════════════════
    obj_asig    = sum(asig_violadas)   * W_ASIG    if asig_violadas  else 0
    obj_eq_sem  = sum(rango_cargas_sem) * W_EQ_SEM  if rango_cargas_sem else 0
    obj_deficit = sum(deficits)       * W_DEFICIT if deficits       else 0
    obj_excess  = sum(excesses)       * W_EXCESO  if excesses       else 0
    obj_equidad = sum(rango_cargas)   * W_EQUIDAD if rango_cargas   else 0
    obj_min_sem = sum(dias_bajo_min)  * W_MIN_SEM if dias_bajo_min  else 0
    obj_max_sem = sum(dias_extra_max) * W_MAX_SEM if dias_extra_max else 0
    obj_frag    = sum(penalizaciones) * W_FRAG    if penalizaciones else 0

    # Reward: favorece asignar cuando hay cobertura requerida ese día y turno
    reward_list = [
        x[w, d, t]
        for d in dias_del_mes
        for t in turnos
        if coberturas_norm[d].get(t, 0) > 0
        for w in trabajadores
    ]
    reward = sum(reward_list) if reward_list else 0

    reward_consecutivo = sum(reward_consec) * W_CONSEC if reward_consec else 0

    model.Minimize(
        obj_asig + obj_deficit + obj_excess +
        obj_equidad + obj_eq_sem +
        obj_min_sem + obj_max_sem + obj_frag
        - reward * W_REWARD
        - reward_consecutivo
    )

    return model, x

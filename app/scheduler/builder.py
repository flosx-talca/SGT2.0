from ortools.sat.python import cp_model
import calendar as cal_module
import math
from collections import defaultdict

# ── Pesos de la función objetivo ─────────────────────────────────────────────
# Separación de órdenes de magnitud garantiza jerarquía estricta.
# Para calibrar el comportamiento del solver, ajustar solo estas constantes.
W_DEFICIT  = 10_000_000   # cobertura mínima — prioridad absoluta
W_EXCESO   =    100_000   # exceso de cobertura
W_EQUIDAD  =    100_000   # equidad mensual por grupo de contrato
W_EQ_SEM   =      5_000   # equidad semanal por grupo de contrato
W_MIN_SEM  =      2_000   # mínimo días/semana según contrato
W_MAX_SEM  =      1_000   # máximo días/semana según contrato
W_FRAG     =        100   # anti-fragmentación (día trabajado aislado)
W_NOCHE    =         10   # balancear turnos noche equitativamente
W_CONSEC   =         50   # reward días consecutivos (agrupa días libres)
W_REWARD   =          1   # utilización del personal disponible
W_ASIG     =  1_000_000   # fijos: muy alto, cede solo ante HR4/HR5/HR7/HR10


def preparar_restricciones(trabajadores_db, dias_del_mes, ausencias):
    """
    Pre-procesamiento ANTES del solver.
    Ahora distingue los 3 tipos de preferencia: FIJO, PREFERENCIA, SOLO_TURNO.
    """
    bloqueados = set()
    fijos      = {}
    turnos_bloqueados_por_dia = {}  # { (worker_id, fecha): set(turnos_permitidos) }

    # Domingos del mes — patrones no aplican domingos
    domingos_mes = {
        d for d in dias_del_mes
        if cal_module.weekday(int(d[:4]), int(d[5:7]), int(d[8:10])) == 6
    }

    for t in trabajadores_db:

        # ── 1. BLOQUEADOS ─────────────────────────────────────────────────────
        for (w_id, fecha_str) in ausencias:
            if w_id == t.id:
                bloqueados.add((t.id, fecha_str))

        # ── Agrupar preferencias por día de semana y tipo ─────────────────────
        prefs_por_dia   = {}  # { dia_semana: { tipo: [turnos] } }
        turnos_solo     = []  # turnos de tipo 'solo_turno'

        for p in t.preferencias:
            if p.tipo == 'solo_turno':
                turnos_solo.append(p.turno)
            else:
                if p.dia_semana not in prefs_por_dia:
                    prefs_por_dia[p.dia_semana] = {'fijo': [], 'preferencia': []}
                # Asegurar que los tipos existan en el dict
                if p.tipo not in prefs_por_dia[p.dia_semana]:
                    prefs_por_dia[p.dia_semana][p.tipo] = []
                prefs_por_dia[p.dia_semana][p.tipo].append(p.turno)

        # ── Procesar FIJOS y PREFERENCIAS por día de semana ───────────────────
        for dia_str in dias_del_mes:
            if dia_str in domingos_mes:
                continue                          # solver maneja domingos
            if (t.id, dia_str) in bloqueados:
                continue                          # bloqueado tiene precedencia

            py_weekday = cal_module.weekday(
                int(dia_str[:4]), int(dia_str[5:7]), int(dia_str[8:10])
            )

            if py_weekday not in prefs_por_dia:
                continue

            prefs_dia = prefs_por_dia[py_weekday]

            # FIJO: DEBE trabajar ese día ese turno
            if prefs_dia.get('fijo'):
                # Solo puede haber 1 turno fijo por día (el primero por seguridad)
                t_fijo = prefs_dia['fijo'][0]
                fijos[(t.id, dia_str)] = t_fijo

            # PREFERENCIA: si trabaja, solo estos turnos
            elif prefs_dia.get('preferencia'):
                key = (t.id, dia_str)
                turnos_bloqueados_por_dia[key] = set(prefs_dia['preferencia'])

        # ── SOLO_TURNO: aplica todos los días ─────────────────────────────────
        # Se guarda temporalmente en el objeto para que planificacion_bp lo lea
        if turnos_solo:
            t._turnos_solo = list(set(turnos_solo))
        else:
            t._turnos_solo = None

    return bloqueados, fijos, turnos_bloqueados_por_dia


def build_model(trabajadores, dias_del_mes, turnos, coberturas,
                bloqueados, fijos,
                turnos_bloqueados_por_dia=None,
                reglas=None, trabajadores_meta=None, turnos_meta=None):
    """
    Construye el modelo CP-SAT mensual de planificación de turnos.

    Recibe bloqueados y fijos desde preparar_restricciones().

    Reglas HARD:
      HR1: Días bloqueados → x=0 (vacaciones, licencias, compensatorios)
      HR2: Días fijos → x=1 en turno fijo (patrones por día de semana)
      HR3: Turnos no permitidos por trabajador → x=0
      HR4: Máximo 1 turno por día por trabajador
      HR5: Tope horas semanales proporcional + horas extra opcionales
      HR6: Máximo días consecutivos configurable por trabajador (default 6)
      HR7: Mínimo domingos libres al mes (configurable, default 2)
      HR8: Cobertura mínima por turno y día
      HR9: Tras turno noche → día siguiente solo noche o descanso
      HR10: Total mensual de turnos según horas contratadas (rango ±1)

    Reglas SOFT (función objetivo):
      SR1 (× 10.000.000): Déficit de cobertura
      SR2 (×   100.000):  Exceso de cobertura
      SR3 (×   100.000):  Equidad mensual por grupo de contrato
      SR4 (×     5.000):  Equidad semanal por grupo de contrato
      SR5 (×     2.000):  Mínimo días/semana
      SR6 (×     1.000):  Máximo días/semana
      SR7 (×       100):  Anti-fragmentación
      SR8 (×        50):  Reward días consecutivos
      SR9 (×        10):  Balancear turnos noche
      SR10(×         1):  Utilización del personal

    Args:
        trabajadores:      lista de IDs
        dias_del_mes:      lista de strings 'YYYY-MM-DD'
        turnos:            lista de abreviaciones de turno
        coberturas:        { turno: req } o { fecha: { turno: req } }
        bloqueados:        set { (worker_id, fecha) }
        fijos:             dict { (worker_id, fecha): turno }
        reglas:            parámetros del cliente desde BD
        trabajadores_meta: { worker_id: { horas_semanales, turnos_permitidos,
                                          permite_horas_extra, max_dias_consecutivos,
                                          duracion_turno } }
        turnos_meta:       { turno: { es_nocturno, horas } }

    Returns:
        model: cp_model.CpModel
        x:     dict { (worker_id, fecha, turno): BoolVar }
    """
    if not trabajadores:
        raise ValueError("build_model: lista de trabajadores vacía")
    if not turnos:
        raise ValueError("build_model: lista de turnos vacía")
    if not dias_del_mes:
        raise ValueError("build_model: lista de días vacía")

    model = cp_model.CpModel()

    if reglas            is None: reglas            = {}
    if trabajadores_meta is None: trabajadores_meta = {}
    if turnos_meta       is None: turnos_meta       = {}

    max_dias_semana  = reglas.get('working_days_limit_max', 6)
    min_domingos_lib = reglas.get('min_free_sundays', 2)
    duracion_default = reglas.get('duracion_turno', 8)
    jornada_default  = reglas.get('jornada_semanal', 42)

    # ── Clasificar turnos ────────────────────────────────────────────────────
    turnos_nocturnos = [
        t for t in turnos
        if turnos_meta.get(t, {}).get('es_nocturno', False)
    ]
    turnos_diurnos = [
        t for t in turnos
        if not turnos_meta.get(t, {}).get('es_nocturno', False)
    ]

    # ── Normalizar coberturas ────────────────────────────────────────────────
    primera = next(iter(coberturas.values()), None)
    if isinstance(primera, dict):
        coberturas_norm = {d: coberturas.get(d, {}) for d in dias_del_mes}
    else:
        coberturas_norm = {d: coberturas for d in dias_del_mes}

    domingos = {
        d for d in dias_del_mes
        if cal_module.weekday(int(d[:4]), int(d[5:7]), int(d[8:10])) == 6
    }

    N = len(dias_del_mes)

    # ── Variables ────────────────────────────────────────────────────────────
    x = {}
    for w in trabajadores:
        for d in dias_del_mes:
            for t in turnos:
                x[w, d, t] = model.NewBoolVar(f'x_{w}_{d}_{t}')

    # ════════════════════════════════════════════════════════════════════════════
    # HR1: BLOQUEADOS → x=0 en todos los turnos
    # ════════════════════════════════════════════════════════════════════════════
    for (w, d) in bloqueados:
        if w in trabajadores and d in dias_del_mes:
            for t in turnos:
                model.Add(x[w, d, t] == 0)

    # ════════════════════════════════════════════════════════════════════════════
    # SR-FIJO: Patrones fijos por día de semana (SOFT con peso muy alto)
    # Es SOFT porque puede entrar en conflicto con:
    #   HR5: tope horas semanales (ej. 30h no puede trabajar 6 días/sem)
    #   HR10: total mensual del contrato
    # Peso W_ASIG = 1.000.000 → el solver los respeta siempre que no viole
    # restricciones contractuales o legales.
    # ════════════════════════════════════════════════════════════════════════════
    fijo_violados = []
    for (w, d), t_fijo in fijos.items():
        if w in trabajadores and d in dias_del_mes and t_fijo in turnos:
            violation = model.NewBoolVar(f'fviol_{w}_{d}')
            model.Add(x[w, d, t_fijo] == 1).OnlyEnforceIf(violation.Not())
            model.Add(x[w, d, t_fijo] == 0).OnlyEnforceIf(violation)
            fijo_violados.append(violation)

    # ════════════════════════════════════════════════════════════════════════════
    # HR2b: PREFERENCIA por día → bloquear turnos NO permitidos ese día
    # Si el trabajador tiene preferencia[lunes] = {M, T}
    # → bloquear I y N ese lunes (pero puede quedar libre)
    # ════════════════════════════════════════════════════════════════════════════
    if turnos_bloqueados_por_dia:
        for (w, d), turnos_permitidos_dia in turnos_bloqueados_por_dia.items():
            if w in trabajadores and d in dias_del_mes:
                for t in turnos:
                    if t not in turnos_permitidos_dia:
                        model.Add(x[w, d, t] == 0)

    # ════════════════════════════════════════════════════════════════════════════
    # HR3: Turnos no permitidos por trabajador
    # ════════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        permitidos = trabajadores_meta.get(w, {}).get('turnos_permitidos', None)
        if permitidos:
            for d in dias_del_mes:
                for t in turnos:
                    if t not in permitidos:
                        model.Add(x[w, d, t] == 0)

    # ════════════════════════════════════════════════════════════════════════════
    # HR4: Máximo 1 turno por día
    # ════════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        for d in dias_del_mes:
            model.AddAtMostOne(x[w, d, t] for t in turnos)

    # ════════════════════════════════════════════════════════════════════════════
    # HR5: Tope horas semanales proporcional
    # HR6: Máximo días consecutivos
    # HR7: Mínimo domingos libres
    # HR9: Post turno noche
    # (agrupados por trabajador para eficiencia)
    # ════════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        meta_w     = trabajadores_meta.get(w, {})
        horas      = meta_w.get('horas_semanales',     jornada_default) or jornada_default
        duracion   = meta_w.get('duracion_turno',      duracion_default) or duracion_default
        extra_ok   = meta_w.get('permite_horas_extra', False)
        max_consec = meta_w.get('max_dias_consecutivos', 6) or 6

        # HR5
        for i in range(0, N, 7):
            semana      = dias_del_mes[i:i + 7]
            n_dias      = len(semana)
            tope_horas  = round(horas * n_dias / 7, 2)
            # Tope base: ceil para no bloquear fijos de 6 días en jornadas no exactas
            #   42h/8h=5.25 → ceil=6 ← necesario para que fijos de 6 días funcionen
            #   20h/8h=2.5  → ceil=3 ← base sin extras
            # permite_horas_extra agrega 1 turno adicional encima del tope base
            #   extra_ok=False: tope = ceil (sin extra)
            #   extra_ok=True:  tope = ceil + 1
            tope_turnos = math.ceil(tope_horas / duracion)
            if extra_ok:
                tope_turnos += 1
            tope_turnos = min(tope_turnos, max_dias_semana)
            model.Add(
                sum(x[w, d, t] for d in semana for t in turnos) <= tope_turnos
            )

        # HR6
        for i in range(N - max_consec):
            ventana = dias_del_mes[i:i + max_consec + 1]
            model.Add(
                sum(x[w, d, t] for d in ventana for t in turnos) <= max_consec
            )

        # HR7
        if domingos:
            max_dom = max(0, len(domingos) - min_domingos_lib)
            model.Add(
                sum(x[w, d, t] for d in domingos for t in turnos) <= max_dom
            )

        # HR9
        if turnos_nocturnos and turnos_diurnos:
            for i in range(N - 1):
                d_hoy    = dias_del_mes[i]
                d_manana = dias_del_mes[i + 1]
                for t_noc in turnos_nocturnos:
                    for t_diurno in turnos_diurnos:
                        model.AddImplication(
                            x[w, d_hoy,    t_noc],
                            x[w, d_manana, t_diurno].Not()
                        )

    # ════════════════════════════════════════════════════════════════════════════
    # HR8: Cobertura mínima por turno y día
    # ════════════════════════════════════════════════════════════════════════════
    deficits = []
    excesses = []
    for d in dias_del_mes:
        cob_hoy = coberturas_norm[d]
        for t in turnos:
            req = cob_hoy.get(t, 0)
            if req > 0:
                assigned = sum(x[w, d, t] for w in trabajadores)
                deficit  = model.NewIntVar(0, req, f'def_{d}_{t}')
                model.Add(assigned + deficit >= req)
                deficits.append(deficit)
                excess = model.NewIntVar(0, len(trabajadores), f'exc_{d}_{t}')
                model.Add(assigned - excess <= req)
                excesses.append(excess)

    # ════════════════════════════════════════════════════════════════════════════
    # HR10: Total mensual según horas contratadas (rango ±1)
    # ceil → empleador asume turno fraccionario
    # ±1 → absorbe conflictos con HR7/HR6/HR2
    # ════════════════════════════════════════════════════════════════════════════
    for w in trabajadores:
        meta_w   = trabajadores_meta.get(w, {})
        horas    = meta_w.get('horas_semanales', jornada_default) or jornada_default
        duracion = meta_w.get('duracion_turno',  duracion_default) or duracion_default

        bloq_w      = sum(1 for (ww, d) in bloqueados if ww == w)
        disponibles = N - bloq_w
        extra_ok    = meta_w.get('permite_horas_extra', False)

        # extra_ok=False → floor: no exceder el contrato
        #   30h/8h=3.75 → floor(16.61) = 16 ✅  round daría 17 ❌
        # extra_ok=True  → ceil: empleador paga la fracción
        #   30h/8h=3.75 → ceil(16.61)  = 17 ✅
        raw_meta     = disponibles / 7 * (horas / duracion)
        meta_mensual = math.ceil(raw_meta) if extra_ok else math.floor(raw_meta)

        if meta_mensual <= 0:
            continue

        total_w  = sum(x[w, d, t] for d in dias_del_mes for t in turnos)
        # Techo siempre exacto (meta sin +1) para no exceder el contrato.
        # Mínimo = meta-1 para absorber domingos libres y ausencias.
        # extra_ok=False: meta=floor → máximo es floor
        # extra_ok=True:  meta=ceil  → máximo es ceil
        model.Add(total_w >= max(0, meta_mensual - 1))
        model.Add(total_w <= min(disponibles, meta_mensual))

    # ════════════════════════════════════════════════════════════════════════════
    # SOFT rules
    # ════════════════════════════════════════════════════════════════════════════

    # SR7: Anti-fragmentación (bidireccional)
    penalizaciones = []
    for w in trabajadores:
        for i in range(1, N - 1):
            ta  = model.NewBoolVar(f'ta_{w}_{i}')
            th  = model.NewBoolVar(f'th_{w}_{i}')
            tm  = model.NewBoolVar(f'tm_{w}_{i}')
            pen = model.NewBoolVar(f'pen_{w}_{i}')
            model.Add(ta == sum(x[w, dias_del_mes[i-1], t] for t in turnos))
            model.Add(th == sum(x[w, dias_del_mes[i],   t] for t in turnos))
            model.Add(tm == sum(x[w, dias_del_mes[i+1], t] for t in turnos))
            model.AddBoolAnd([ta.Not(), th, tm.Not()]).OnlyEnforceIf(pen)
            model.AddBoolOr([ta, th.Not(), tm]).OnlyEnforceIf(pen.Not())
            penalizaciones.append(pen)

    # SR9: Balancear turnos noche
    pen_noche = []
    if turnos_nocturnos:
        for w in trabajadores:
            total_noches = sum(
                x[w, d, t]
                for d in dias_del_mes
                for t in turnos_nocturnos
            )
            pen_noche.append(total_noches)

    # Equidad mensual por grupo
    grupos = defaultdict(list)
    for w in trabajadores:
        h = (trabajadores_meta.get(w, {}).get('horas_semanales', jornada_default)
             or jornada_default)
        grupos[h].append(w)

    rango_cargas = []
    for h_grupo, ws in grupos.items():
        if len(ws) < 2:
            continue
        max_g = model.NewIntVar(0, N, f'max_c_{h_grupo}')
        min_g = model.NewIntVar(0, N, f'min_c_{h_grupo}')
        for w in ws:
            tw = sum(x[w, d, t] for d in dias_del_mes for t in turnos)
            model.Add(tw <= max_g)
            model.Add(tw >= min_g)
        rg = model.NewIntVar(0, N, f'rng_{h_grupo}')
        model.Add(rg == max_g - min_g)
        rango_cargas.append(rg)

    # Equidad semanal por grupo
    rango_cargas_sem = []
    for h_grupo, ws in grupos.items():
        if len(ws) < 2:
            continue
        for i in range(0, N, 7):
            sem = dias_del_mes[i:i + 7]
            if not sem:
                continue
            max_s = model.NewIntVar(0, 7, f'max_s_{h_grupo}_{i}')
            min_s = model.NewIntVar(0, 7, f'min_s_{h_grupo}_{i}')
            for w in ws:
                ds = sum(x[w, d, t] for d in sem for t in turnos)
                model.Add(ds <= max_s)
                model.Add(ds >= min_s)
            rs = model.NewIntVar(0, 7, f'rng_s_{h_grupo}_{i}')
            model.Add(rs == max_s - min_s)
            rango_cargas_sem.append(rs)

    # Mín/Máx semanal
    dias_bajo_min  = []
    dias_extra_max = []
    for w in trabajadores:
        meta_w   = trabajadores_meta.get(w, {})
        horas    = meta_w.get('horas_semanales', jornada_default) or jornada_default
        duracion = meta_w.get('duracion_turno',  duracion_default) or duracion_default
        min_w    = math.floor(horas / duracion)
        lim_w    = min(math.ceil(horas / duracion), max_dias_semana)

        for i in range(N - 6):
            v7  = dias_del_mes[i:i + 7]
            aus = sum(1 for d in v7 if (w, d) in bloqueados)
            tw  = sum(x[w, d, t] for d in v7 for t in turnos)
            if (7 - aus) >= min_w:
                ft = model.NewIntVar(0, min_w, f'bmin_{w}_{i}')
                model.Add(tw + ft >= min_w)
                dias_bajo_min.append(ft)
            ex = model.NewIntVar(0, 7, f'emax_{w}_{i}')
            model.Add(tw - lim_w <= ex)
            dias_extra_max.append(ex)

    # SR8: Reward días consecutivos
    reward_consec = []
    for w in trabajadores:
        for i in range(N - 1):
            th  = model.NewBoolVar(f'cth_{w}_{i}')
            tm  = model.NewBoolVar(f'ctm_{w}_{i}')
            par = model.NewBoolVar(f'par_{w}_{i}')
            model.Add(th == sum(x[w, dias_del_mes[i],   t] for t in turnos))
            model.Add(tm == sum(x[w, dias_del_mes[i+1], t] for t in turnos))
            model.AddBoolAnd([th, tm]).OnlyEnforceIf(par)
            model.AddBoolOr([th.Not(), tm.Not()]).OnlyEnforceIf(par.Not())
            reward_consec.append(par)

    # SR10: Reward utilización
    reward_list = [
        x[w, d, t]
        for d in dias_del_mes
        for t in turnos
        if coberturas_norm[d].get(t, 0) > 0
        for w in trabajadores
    ]

    # ── Función objetivo ─────────────────────────────────────────────────────
    model.Minimize(
        (sum(fijo_violados)    * W_ASIG    if fijo_violados    else 0) +
        (sum(deficits)         * W_DEFICIT if deficits         else 0) +
        (sum(excesses)         * W_EXCESO  if excesses         else 0) +
        (sum(rango_cargas)     * W_EQUIDAD if rango_cargas     else 0) +
        (sum(rango_cargas_sem) * W_EQ_SEM  if rango_cargas_sem else 0) +
        (sum(dias_bajo_min)    * W_MIN_SEM if dias_bajo_min    else 0) +
        (sum(dias_extra_max)   * W_MAX_SEM if dias_extra_max   else 0) +
        (sum(penalizaciones)   * W_FRAG    if penalizaciones   else 0) +
        (sum(pen_noche)        * W_NOCHE   if pen_noche        else 0) -
        (sum(reward_list)      * W_REWARD  if reward_list      else 0) -
        (sum(reward_consec)    * W_CONSEC  if reward_consec    else 0)
    )

    return model, x

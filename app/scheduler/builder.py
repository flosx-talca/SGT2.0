from ortools.sat.python import cp_model
import calendar as cal_module
import math
from datetime import datetime, timedelta
from collections import defaultdict
from app.services.config_manager import ConfigManager
from app.services.legal_engine import LegalEngine
from app.models.enums import RestrictionType, TipoContrato

# ── Pesos de la función objetivo ─────────────────────────────────────────────
# Leer desde BD — ConfigManager.preload() se llama al inicio de build_model()
# Los valores por defecto aquí son solo fallback de emergencia
W_DEFICIT      = None
W_EXCESO       = None
W_EQUIDAD      = None
W_META         = None
W_REWARD       = None
W_NOCHE_REWARD = None

# ── SGT 2.1: Defaults para pesos adicionales ────────────────────────────────
DEFAULT_PENALTY_CAMBIO_TURNO = 150
DEFAULT_PENALTY_TURNO_AISLADO = 200
DEFAULT_BONUS_TURNO_DOMINANTE = 80
DEFAULT_PENALTY_NO_PREFERENTE = 500


def _get_mock_turno_worker(w, trabajadores_meta, turnos_meta):
    """Retorna MockTurno con la duración representativa para el worker."""
    meta_w      = trabajadores_meta.get(w, {})
    permitidos  = meta_w.get('turnos_permitidos', None)

    if permitidos:
        horas_list = [turnos_meta[t]['horas'] for t in permitidos if t in turnos_meta]
    else:
        horas_list = [v['horas'] for v in turnos_meta.values() if v.get('horas')]

    duracion = round(sum(horas_list) / len(horas_list), 1) if horas_list else 8.0
    
    class MockTurnoLocal:
        def __init__(self, d):
            self.duracion_hrs = d
            self.es_nocturno = False
    return MockTurnoLocal(duracion)


def dividir_en_semanas(fecha_inicio, fecha_fin):
    """Divide un rango de fechas en semanas ISO (lun-dom)."""
    semanas = []
    dia = fecha_inicio
    while dia <= fecha_fin:
        wd = dia.weekday()
        fin_semana = dia + timedelta(days=6 - wd)
        fin_real = min(fin_semana, fecha_fin)
        semana = [dia + timedelta(days=i) for i in range((fin_real - dia).days + 1)]
        semanas.append(semana)
        dia = fin_real + timedelta(days=1)
    return semanas


def preparar_restricciones(trabajadores_db, dias_del_mes, ausencias, restricciones_especiales=None):
    """Pre-procesamiento de restricciones para el solver."""
    if restricciones_especiales is None: restricciones_especiales = []
    
    bloqueados = set()
    fijos      = {}
    turnos_bloqueados_por_dia = {}  # { (worker_id, fecha_str): set(turnos_permitidos) }
    restricciones_hard = []
    restricciones_soft = []

    for t in trabajadores_db:
        # 1. AUSENCIAS
        for (w_id, fecha_str) in ausencias:
            if w_id == t.id:
                bloqueados.add((t.id, fecha_str))

        # 2. RESTRICCIONES ESPECIALES SGT 2.1 (Unificadas)
        for r in [res for res in restricciones_especiales if res.trabajador_id == t.id]:
            curr = r.fecha_inicio
            while curr <= r.fecha_fin:
                if r.dias_semana is None or curr.weekday() in r.dias_semana:
                    d_str = curr.isoformat()
                    if d_str in dias_del_mes and (t.id, d_str) not in bloqueados:
                        # Bug fix: normalizar r.tipo a string para comparación robusta
                        r_tipo_str = str(r.tipo.value if hasattr(r.tipo, 'value') else r.tipo)

                        # SGT 2.1: PROTECCIÓN DOMINGOS - Nunca permitir TURNO_FIJO en domingo
                        if r_tipo_str == RestrictionType.TURNO_FIJO.value and curr.weekday() == 6:
                            curr += timedelta(days=1)
                            continue

                        if r_tipo_str == RestrictionType.TURNO_FIJO.value and r.turno:
                            fijos[(t.id, d_str)] = r.turno.abreviacion
                        elif r_tipo_str == RestrictionType.SOLO_TURNO.value and r.turno:
                            turnos_bloqueados_por_dia[(t.id, d_str)] = {r.turno.abreviacion}
                        elif r_tipo_str == RestrictionType.EXCLUIR_TURNO.value and r.turno:
                            restricciones_hard.append({'w': t.id, 'd': d_str, 't': r.turno.abreviacion, 'action': 'exclude'})
                        elif r_tipo_str == RestrictionType.TURNO_PREFERENTE.value and r.turno:
                            restricciones_soft.append({'w': t.id, 'd': d_str, 't': r.turno.abreviacion, 'type': 'preferente'})
                curr += timedelta(days=1)

    return bloqueados, fijos, turnos_bloqueados_por_dia, restricciones_hard, restricciones_soft


def build_model(trabajadores, dias_del_mes, turnos, coberturas,
                bloqueados, fijos,
                turnos_bloqueados_por_dia=None,
                restricciones_hard=None, restricciones_soft=None,
                reglas=None, trabajadores_meta=None, turnos_meta=None):
    """Construye el modelo CP-SAT para planificación de turnos."""
    if not trabajadores or not turnos or not dias_del_mes:
        raise ValueError("build_model: Parámetros de entrada insuficientes")

    model = cp_model.CpModel()
    if reglas is None: reglas = {}
    if trabajadores_meta is None: trabajadores_meta = {}
    if turnos_meta is None: turnos_meta = {}
    if restricciones_hard is None: restricciones_hard = []
    if restricciones_soft is None: restricciones_soft = []

    ConfigManager.preload()
    
    # Cargar pesos desde BD
    global W_DEFICIT, W_EXCESO, W_EQUIDAD, W_META, W_REWARD, W_NOCHE_REWARD
    W_DEFICIT      = ConfigManager.get_int('W_DEFICIT',      10_000_000)
    W_EXCESO       = ConfigManager.get_int('W_EXCESO',          100_000)
    W_EQUIDAD      = ConfigManager.get_int('W_EQUIDAD',       1_000_000)
    W_META         = ConfigManager.get_int('W_META',             50_000)
    W_REWARD       = ConfigManager.get_int('W_REWARD',           10_000)
    W_NOCHE_REWARD = ConfigManager.get_int('W_NOCHE_REWARD',     20_000)
    
    est_penalties, est_bonus, pref_penalties = [], [], []
    
    # Estos se mantienen como fallback o se pueden migrar luego
    W_EQ_SEM   = ConfigManager.get_int('W_EQ_SEM', 5_000)
    W_MIN_SEM  = ConfigManager.get_int('W_MIN_SEM', 2_000)
    W_MAX_SEM  = ConfigManager.get_int('W_MAX_SEM', 1_000)
    W_FRAG     = ConfigManager.get_int('W_FRAG', 100)
    W_BALANCE  = ConfigManager.get_int('W_BALANCE', 3_000)
    W_EXCESO_HORAS = ConfigManager.get_int('W_EXCESO_HORAS', 20_000_000)
    W_DOMINGO  = ConfigManager.get_int('W_DOMINGO', 50_000_000)

    duracion_default = ConfigManager.get_int('DURACION_TURNO_PROMEDIO', 8)
    jornada_default  = ConfigManager.get('MAX_HRS_SEMANA_FULL', 42.0)

    # ── 3. Pre-validaciones ───────────────────────────────────
    class MockWorker:
        def __init__(self, meta):
            tc = meta.get('tipo_contrato', TipoContrato.FULL_TIME)
            if isinstance(tc, str):
                try:
                    self.tipo_contrato = TipoContrato[tc.upper()]
                except:
                    self.tipo_contrato = next((e for e in TipoContrato if e.value == tc.lower()), TipoContrato.FULL_TIME)
            else:
                self.tipo_contrato = tc
            
            self.horas_semanales = float(meta.get('horas_semanales', 42.0))
            self.permite_horas_extra = bool(meta.get('permite_horas_extra', False))

    class MockTurno:
        def __init__(self, m):
            self.nombre = m.get('nombre', 'T')
            self.duracion_hrs = float(m.get('horas', 8.0))
            self.es_nocturno = bool(m.get('es_nocturno', False))

    for w in trabajadores:
        meta_w = trabajadores_meta.get(w, {})
        w_obj = MockWorker(meta_w)
        for t_id, t_meta in turnos_meta.items():
            if not t_meta: continue
            ok, motivo = LegalEngine.turno_compatible(w_obj, MockTurno(t_meta))
            if not ok:
                print(f"[PRE-CHECK] Incompatible: Worker {w} + Shift {t_id}: {motivo}")

    turnos_nocturnos = [t for t in turnos if turnos_meta.get(t, {}).get('es_nocturno', False)]
    turnos_diurnos = [t for t in turnos if not turnos_meta.get(t, {}).get('es_nocturno', False)]

    primera = next(iter(coberturas.values()), None)
    coberturas_norm = {d: (coberturas.get(d, {}) if isinstance(primera, dict) else coberturas) for d in dias_del_mes}
    domingos = {d for d in dias_del_mes if datetime.strptime(d, '%Y-%m-%d').weekday() == 6}
    N = len(dias_del_mes)

    x = {}
    for w in trabajadores:
        for d in dias_del_mes:
            for t in turnos:
                x[w, d, t] = model.NewBoolVar(f'x_{w}_{d}_{t}')

    # HR1: Bloqueados
    for (w, d) in bloqueados:
        if w in trabajadores and d in dias_del_mes:
            for t in turnos: model.Add(x[w, d, t] == 0)

    # HR1b: Dotación 0
    for d in dias_del_mes:
        for t in turnos:
            if coberturas_norm[d].get(t, 0) == 0:
                for w in trabajadores:
                    if (w, d) not in bloqueados: model.Add(x[w, d, t] == 0)

    # HR2: Fijos (Soft Presence, Hard Turn Type)
    fijos_penalties = []
    for (w, d), t_fijo in fijos.items():
        if w in trabajadores and d in dias_del_mes and t_fijo in turnos:
            # Hard: Si trabaja, DEBE ser t_fijo
            for t_idx in turnos:
                if t_idx != t_fijo:
                    model.Add(x[w, d, t_idx] == 0)
            
            # HARD: Forzar que el trabajador TRABAJE en t_fijo ese día
            # (No es soft/penalty — es una obligación que no puede ignorarse)
            model.Add(x[w, d, t_fijo] == 1)

    # HR2b: Preferencia por día
    if turnos_bloqueados_por_dia:
        for (w, d), permitidos in turnos_bloqueados_por_dia.items():
            if w in trabajadores and d in dias_del_mes:
                for t in turnos:
                    if t not in permitidos: model.Add(x[w, d, t] == 0)

    # HR3: Restricciones Especiales HARD
    for rh in restricciones_hard:
        w, d, action = rh['w'], rh['d'], rh['action']
        if w not in trabajadores or d not in dias_del_mes: continue
        if action == 'exclude':
            t_exc = rh['t']
            if t_exc in turnos: model.Add(x[w, d, t_exc] == 0)

    # HR4: Máximo 1 turno por día
    for w in trabajadores:
        for d in dias_del_mes: model.AddAtMostOne(x[w, d, t] for t in turnos)

    # HR5-HR9: Reglas Legales y de Descanso
    f_inicio = datetime.strptime(dias_del_mes[0], '%Y-%m-%d').date()
    f_fin = datetime.strptime(dias_del_mes[-1], '%Y-%m-%d').date()
    semanas_objs = dividir_en_semanas(f_inicio, f_fin)

    for w in trabajadores:
        meta_w = trabajadores_meta.get(w, {})
        w_obj = MockWorker(meta_w)
        mock_turno_w = _get_mock_turno_worker(w, trabajadores_meta, turnos_meta)
        res_w = LegalEngine.resumen_legal(w_obj, mock_turno_w, 7) # Perfil legal estándar
        max_consec = meta_w.get('max_dias_consecutivos', 6) or 6

        for sem in semanas_objs:
            s_strs = [d.isoformat() for d in sem if d.isoformat() in dias_del_mes]
            if not s_strs: continue
            res = LegalEngine.resumen_legal(w_obj, mock_turno_w, len(s_strs))
            print(f"[DEBUG] Worker {w} Week {s_strs[0]}: max_hrs={res['max_horas_semana']} max_dias={res['max_dias_semana']}")
            # SGT 2.1: Convertir límite de horas en SOFT para evitar INFEASIBLE por turnos fijos
            max_hrs_val = int(res['max_horas_semana'] * 10)
            h_asig = [x[w, d, t] * int(turnos_meta.get(t, {}).get('horas', 8.0) * 10) for d in s_strs for t in turnos]
            h_total_sem = sum(h_asig)
            
            # Variable de exceso de horas (Soft)
            permite_extra = getattr(w_obj, 'permite_horas_extra', False)
            if permite_extra:
                max_extra_val = 100 # 10h extra
                exceso_h = model.NewIntVar(0, max_extra_val, f'exc_h_{w}_{s_strs[0]}')
                model.Add(h_total_sem <= max_hrs_val + exceso_h)
                est_penalties.append(exceso_h * W_EXCESO_HORAS)
            else:
                # Si no permite extra, es una restricción HARD
                model.Add(h_total_sem <= max_hrs_val)

            model.Add(sum(x[w, d, t] for d in s_strs for t in turnos) <= res['max_dias_semana'])

        if domingos:
            # [HR7] Domingos libres obligatorios (Art. 38 inc. 4° CT)
            # Aplica si: empresa en régimen exceptuado AND jornada > 20h/semana (UMBRAL_HRS_DOMINGO_OBLIGATORIO)
            aplica = res_w.get('aplica_domingo', False)
            if aplica:
                min_libres = res_w.get('min_domingos_mes', 2) or 2
                
                # SGT 2.1 (INC-04a): Descontar domingos bloqueados por ausencia.
                # Los domingos con ausencia NO cuentan como "otorgados" según jurisprudencia DT.
                domingos_disponibles = [
                    d for d in domingos
                    if (w, d) not in bloqueados
                ]
                max_asig_dom = max(0, len(domingos_disponibles) - min_libres)
                
                # HARD: No puede trabajar más de (domingos_disponibles - min_libres) domingos
                asig_dom = sum(x[w, d, t] for d in domingos_disponibles for t in turnos)
                model.Add(asig_dom <= max_asig_dom)

        # [HR11] Máximo 3 domingos consecutivos trabajados (Art. 38 inc. 5° CT)
        # Solo aplica a trabajadores con HR7 activo (régimen exceptuado + jornada > 20h)
        if res_w.get('aplica_domingo', False):
            domingos_todos = sorted(domingos)
            max_dom_consec = ConfigManager.get_int('MAX_DOMINGOS_CONSECUTIVOS', 3)
            for i in range(len(domingos_todos) - max_dom_consec):
                ventana = domingos_todos[i : i + max_dom_consec + 1]
                model.Add(
                    sum(x[w, d, t] for d in ventana for t in turnos) <= max_dom_consec
                )

        for i in range(N - max_consec):
            vent = dias_del_mes[i : i + max_consec + 1]
            model.Add(sum(x[w, d, t] for d in vent for t in turnos) <= max_consec)

        if turnos_nocturnos and turnos_diurnos:
            for i in range(N - 1):
                d1, d2 = dias_del_mes[i], dias_del_mes[i+1]
                for tn in turnos_nocturnos:
                    for td in turnos_diurnos: model.AddImplication(x[w, d1, tn], x[w, d2, td].Not())

    # HR8: Cobertura
    deficits, excesses = [], []
    req_total_global = 0
    for d in dias_del_mes:
        for t in turnos:
            req = coberturas_norm[d].get(t, 0)
            if req > 0:
                req_total_global += req
                asig = sum(x[w, d, t] for w in trabajadores)
                defic = model.NewIntVar(0, req, f'def_{d}_{t}')
                model.Add(asig + defic >= req)
                
                # Priorizar noches en cobertura (Déficit de noche es el doble de caro)
                is_noche = turnos_meta.get(t, {}).get('es_nocturno', False)
                w_def = W_DEFICIT * 2 if is_noche else W_DEFICIT
                deficits.append(defic * w_def) # El peso ya se incluye aquí
                
                exce = model.NewIntVar(0, len(trabajadores), f'exc_{d}_{t}')
                model.Add(asig - exce <= req)
                excesses.append(exce * W_EXCESO)  # Penalización baja por sobredotación

    # HR10: Meta mensual y Equidad
    desviaciones_meta = []
    totales_w = {}
    for w in trabajadores:
        meta_w = trabajadores_meta.get(w, {})
        res_w = LegalEngine.resumen_legal(MockWorker(meta_w), _get_mock_turno_worker(w, trabajadores_meta, turnos_meta), 7)
        disponibles = N - sum(1 for (ww, d) in bloqueados if ww == w)
        meta_m = math.floor((disponibles / 7.0) * res_w['max_dias_semana'])
        
        total_w = sum(x[w, d, t] for d in dias_del_mes for t in turnos)
        totales_w[w] = total_w
        
        # Meta mensual SOFT: penalizar desviaciones
        desv = model.NewIntVar(0, disponibles, f'dev_meta_{w}')
        model.AddAbsEquality(desv, total_w - meta_m)
        desviaciones_meta.append(desv)

    # Equidad mensual por grupo (FULL_TIME vs PART_TIME)
    rango_cargas = []
    grupos = defaultdict(list)
    for w in trabajadores:
        meta_w = trabajadores_meta.get(w, {})
        grupos[meta_w.get('tipo_contrato', 'FULL_TIME')].append(w)
    
    for g_name, g_workers in grupos.items():
        if len(g_workers) >= 2:
            max_g = model.NewIntVar(0, N, f'max_g_{g_name}')
            min_g = model.NewIntVar(0, N, f'min_g_{g_name}')
            for w in g_workers:
                model.Add(totales_w[w] <= max_g)
                model.Add(totales_w[w] >= min_g)
            rng = model.NewIntVar(0, N, f'rng_g_{g_name}')
            model.Add(rng == max_g - min_g)
            rango_cargas.append(rng)

    # SOFT rules
    w_cambio = ConfigManager.get_int('W_CAMBIO_TURNO', DEFAULT_PENALTY_CAMBIO_TURNO)
    w_dominante = ConfigManager.get_int('W_TURNO_DOMINANTE', DEFAULT_BONUS_TURNO_DOMINANTE)
    w_no_pref = ConfigManager.get_int('W_NO_PREFERENTE', DEFAULT_PENALTY_NO_PREFERENTE)

    for w in trabajadores:
        for t in turnos:
            worked_t = [x[w, d, t] for d in dias_del_mes]
            for i in range(N - 1):
                cambio = model.NewBoolVar(f'cambio_{w}_{dias_del_mes[i]}_{t}')
                model.AddBoolAnd([worked_t[i], worked_t[i+1].Not()]).OnlyEnforceIf(cambio)
                est_penalties.append(cambio * w_cambio)
            is_dom = model.NewBoolVar(f'dominant_{w}_{t}')
            total_w = totales_w[w]
            model.Add(sum(worked_t) * 2 >= total_w).OnlyEnforceIf(is_dom)
            est_bonus.append(is_dom * w_dominante)

    for rs in restricciones_soft:
        w, d, tp = rs['w'], rs['d'], rs['t']
        if w in trabajadores and d in dias_del_mes and tp in turnos:
            is_wd = sum(x[w, d, tt] for tt in turnos)
            not_p = model.NewBoolVar(f'not_pref_{w}_{d}')
            model.AddBoolAnd([is_wd, x[w, d, tp].Not()]).OnlyEnforceIf(not_p)
            pref_penalties.append(not_p * w_no_pref)

    penalizaciones_frag = []
    for w in trabajadores:
        for i in range(1, N - 1):
            ta, th, tm = model.NewBoolVar(f'ta_{w}_{i}'), model.NewBoolVar(f'th_{w}_{i}'), model.NewBoolVar(f'tm_{w}_{i}')
            pen = model.NewBoolVar(f'pen_{w}_{i}')
            model.Add(ta == sum(x[w, dias_del_mes[i-1], tt] for tt in turnos))
            model.Add(th == sum(x[w, dias_del_mes[i], tt] for tt in turnos))
            model.Add(tm == sum(x[w, dias_del_mes[i+1], tt] for tt in turnos))
            model.AddBoolAnd([ta.Not(), th, tm.Not()]).OnlyEnforceIf(pen)
            penalizaciones_frag.append(pen * W_FRAG)

    # SR-BALANCE: Equidad de distribución de turnos por tipo
    balance_por_turno = []
    if len(trabajadores) >= 2:
        for t in turnos:
            totales_t = [sum(x[w, d, t] for d in dias_del_mes) for w in trabajadores]
            max_t = model.NewIntVar(0, N, f'max_bal_{t}')
            min_t = model.NewIntVar(0, N, f'min_bal_{t}')
            for tw in totales_t:
                model.Add(tw <= max_t)
                model.Add(tw >= min_t)
            rango_t = model.NewIntVar(0, N, f'rng_bal_{t}')
            model.Add(rango_t == max_t - min_t)
            balance_por_turno.append(rango_t)

    # SR-DOMINANTE: Bonus por turno dominante
    # SGT 2.1: Incluir incentivo extra para noches
    reward_list = []
    for d in dias_del_mes:
        for t in turnos:
            if coberturas_norm[d].get(t, 0) > 0:
                is_noche = turnos_meta.get(t, {}).get('es_nocturno', False)
                w_r = W_NOCHE_REWARD if is_noche else W_REWARD
                for w in trabajadores:
                    reward_list.append(x[w, d, t] * w_r)

    model.Minimize(
        # deficits ya tiene W_DEFICIT multiplicado; excesses ya tiene W_EXCESO multiplicado
        sum(deficits) + sum(excesses) +
        (sum(rango_cargas) * W_EQUIDAD) + (sum(balance_por_turno) * W_BALANCE) +
        (sum(desviaciones_meta) * W_META) + (sum(est_penalties)) +
        (sum(pref_penalties)) + (sum(penalizaciones_frag)) -
        (sum(est_bonus)) - (sum(reward_list))
    )

    model._debug_meta = {w: {'horas': trabajadores_meta.get(w, {}).get('horas_semanales', jornada_default), 'duracion': trabajadores_meta.get(w, {}).get('duracion_turno', duracion_default)} for w in trabajadores}
    model._debug_workers, model._debug_dias, model._debug_turnos, model._debug_coberturas = trabajadores, dias_del_mes, turnos, coberturas_norm
    return model, x

"""
Motor genérico de evaluación de reglas SGT.

Uso:
    from app.services.rule_engine import evaluate_rule
    passed, detail = evaluate_rule(rule_dict, ctx)

rule_dict: {family, code, rule_type, scope, field, operator, params}
ctx:       dict con los valores del contexto a evaluar (worker, date, sequence, etc.)
"""
import operator as _op
from datetime import date as _date

_OPS = {
    '==': _op.eq,
    '!=': _op.ne,
    '>':  _op.gt,
    '<':  _op.lt,
    '>=': _op.ge,
    '<=': _op.le,
}


def evaluate_rule(rule, ctx):
    family = rule.get('family')
    _evaluators = {
        'comparison':            eval_comparison,
        'range':                 eval_range,
        'set_membership':        eval_set_membership,
        'sequence':              eval_sequence,
        'logic_all_any_not':     eval_logic,
        'calendar':              eval_calendar,
        'worker_attribute':      eval_worker_attribute,
        'assignment_constraint': eval_assignment_constraint,
    }
    fn = _evaluators.get(family)
    if not fn:
        raise ValueError(f'Familia de regla desconocida: {family}')
    return fn(rule, ctx)


def eval_comparison(rule, ctx):
    field = rule.get('field')
    operator_str = rule.get('operator', '<=')
    threshold = rule.get('params', {}).get('value')
    val = ctx.get(field)
    if val is None or threshold is None:
        return False, f'Campo "{field}" o umbral no disponible en contexto.'
    fn = _OPS.get(operator_str)
    if not fn:
        return False, f'Operador "{operator_str}" no soportado.'
    passed = fn(val, threshold)
    return passed, f'{field}={val} {operator_str} {threshold} → {"OK" if passed else "FALLA"}'


def eval_range(rule, ctx):
    field = rule.get('field')
    params = rule.get('params', {})
    min_val = params.get('min')
    max_val = params.get('max')
    val = ctx.get(field)
    if val is None:
        return False, f'Campo "{field}" no disponible en contexto.'
    passed = (min_val is None or val >= min_val) and (max_val is None or val <= max_val)
    return passed, f'{field}={val} en [{min_val}, {max_val}] → {"OK" if passed else "FALLA"}'


def eval_set_membership(rule, ctx):
    field = rule.get('field')
    params = rule.get('params', {})
    values = params.get('values', [])
    operator_str = rule.get('operator', 'in')
    val = ctx.get(field)
    if val is None:
        return False, f'Campo "{field}" no disponible en contexto.'
    in_set = val in values
    passed = in_set if operator_str == 'in' else not in_set
    label = 'in' if operator_str == 'in' else 'not in'
    return passed, f'{field}={val} {label} {values} → {"OK" if passed else "FALLA"}'


def eval_sequence(rule, ctx):
    """
    ctx['sequence']: lista de booleans (True=trabaja) para el período.
    params: max_days (hard) o preferred_min_days/preferred_max_days (soft)
    """
    sequence = ctx.get('sequence', [])
    if not sequence:
        return True, 'Sin secuencia para evaluar.'
    params = rule.get('params', {})
    max_days = params.get('max_days') or params.get('value')
    max_consecutive = 0
    current = 0
    for day in sequence:
        if day:
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    if max_days is not None:
        passed = max_consecutive <= max_days
        return passed, f'Máx consecutivos={max_consecutive}, límite={max_days} → {"OK" if passed else "FALLA"}'
    return True, f'Máx consecutivos={max_consecutive}'


def eval_logic(rule, ctx):
    params = rule.get('params', {})
    logic_op = params.get('logic', 'all')
    sub_rules = params.get('rules', [])
    if not sub_rules:
        return True, 'Sin sub-reglas.'
    results = [evaluate_rule(r, ctx) for r in sub_rules]
    passed_list = [r[0] for r in results]
    if logic_op == 'all':
        passed = all(passed_list)
    elif logic_op == 'any':
        passed = any(passed_list)
    elif logic_op == 'not':
        passed = not passed_list[0] if passed_list else True
    else:
        return False, f'Operador lógico "{logic_op}" no soportado.'
    details = ', '.join(r[1] for r in results)
    return passed, f'{logic_op}({details}) → {"OK" if passed else "FALLA"}'


def eval_calendar(rule, ctx):
    params = rule.get('params', {})
    evaluate = params.get('evaluate', 'holiday')
    check_date = ctx.get('date')
    holidays = ctx.get('holidays', [])
    if check_date is None:
        return True, 'Sin fecha para evaluar.'
    if isinstance(check_date, str):
        check_date = _date.fromisoformat(check_date)
    if evaluate == 'holiday':
        is_holiday = check_date in holidays
        return not is_holiday, f'{check_date} es feriado → {"FALLA" if is_holiday else "OK"}'
    if evaluate == 'sunday':
        is_sunday = check_date.weekday() == 6
        return not is_sunday, f'{check_date} es domingo → {"FALLA" if is_sunday else "OK"}'
    if evaluate == 'weekend':
        is_weekend = check_date.weekday() >= 5
        return not is_weekend, f'{check_date} es fin de semana → {"FALLA" if is_weekend else "OK"}'
    return True, f'Tipo "{evaluate}" no reconocido.'


def eval_worker_attribute(rule, ctx):
    field = rule.get('field')
    params = rule.get('params', {})
    expected = params.get('value')
    operator_str = rule.get('operator', '==')
    worker = ctx.get('worker', {})
    val = worker.get(field)
    if val is None:
        return False, f'Atributo "{field}" no disponible en trabajador.'
    fn = _OPS.get(operator_str)
    if not fn:
        return False, f'Operador "{operator_str}" no soportado.'
    passed = fn(val, expected)
    return passed, f'worker.{field}={val} {operator_str} {expected} → {"OK" if passed else "FALLA"}'


def eval_assignment_constraint(rule, ctx):
    params = rule.get('params', {})
    constraint = params.get('constraint')
    if constraint == 'no_double_shift':
        assignments_today = ctx.get('assignments_today', 0)
        passed = assignments_today < 1
        return passed, f'Asignaciones hoy={assignments_today} → {"OK" if passed else "DOBLE TURNO"}'
    if constraint == 'min_coverage':
        required = params.get('min_coverage', 1)
        current = ctx.get('coverage_count', 0)
        passed = current >= required
        return passed, f'Cobertura={current}/{required} → {"OK" if passed else "FALLA"}'
    if constraint == 'area_match':
        worker_area = ctx.get('worker_area')
        shift_area = ctx.get('shift_area')
        passed = worker_area == shift_area or ctx.get('cross_area_authorized', False)
        return passed, f'Área worker={worker_area} / turno={shift_area} → {"OK" if passed else "FALLA"}'
    return True, f'Restricción "{constraint}" no implementada.'

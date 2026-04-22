from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import ReglaFamilia, ReglaCatalogo, ReglaEmpresa, Empresa
from datetime import datetime
import json

regla_bp = Blueprint('regla', __name__, url_prefix='/reglas')

# ─── FAMILIAS ────────────────────────────────────────────────────────────────

@regla_bp.route('/familias')
def familias():
    registros = ReglaFamilia.query.order_by(ReglaFamilia.nombre).all()
    return render_template('reglas-familias.html', registros=registros)

@regla_bp.route('/familias/modal', methods=['POST'])
def familias_modal():
    modo = request.form.get('modo', 'Agregar')
    rid = request.form.get('id', None)
    registro = ReglaFamilia.query.get(int(rid)) if rid and rid != '0' else None
    return render_template('modal-regla-familia.html', modo=modo, registro=registro)

@regla_bp.route('/familias/guardar', methods=['POST'])
def familias_guardar():
    rid = request.form.get('id', '').strip()
    codigo = request.form.get('codigo', '').strip()
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    activo = request.form.get('activo') == 'true'

    if not codigo or not nombre:
        return jsonify({'ok': False, 'msg': 'Código y Nombre son obligatorios.'}), 400

    try:
        if rid and rid != '0':
            reg = ReglaFamilia.query.get_or_404(int(rid))
            reg.codigo = codigo
            reg.nombre = nombre
            reg.descripcion = descripcion
            reg.activo = activo
            msg = f'Familia "{nombre}" actualizada.'
        else:
            if ReglaFamilia.query.filter_by(codigo=codigo).first():
                return jsonify({'ok': False, 'msg': f'Ya existe una familia con el código "{codigo}".'}), 400
            reg = ReglaFamilia(codigo=codigo, nombre=nombre, descripcion=descripcion, activo=activo)
            db.session.add(reg)
            msg = f'Familia "{nombre}" creada.'
        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@regla_bp.route('/familias/toggle', methods=['POST'])
def familias_toggle():
    rid = request.form.get('id', '').strip()
    reg = ReglaFamilia.query.get_or_404(int(rid))
    reg.activo = not reg.activo
    db.session.commit()
    estado = 'activada' if reg.activo else 'desactivada'
    return jsonify({'ok': True, 'msg': f'Familia {estado}.', 'activo': reg.activo})


# ─── CATÁLOGO DE REGLAS ───────────────────────────────────────────────────────

@regla_bp.route('/catalogo')
def catalogo():
    registros = ReglaCatalogo.query.order_by(ReglaCatalogo.nombre).all()
    familias = ReglaFamilia.query.filter_by(activo=True).order_by(ReglaFamilia.nombre).all()
    empresas = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('reglas-config.html', registros=registros, familias=familias, empresas=empresas)

@regla_bp.route('/catalogo/modal', methods=['POST'])
def catalogo_modal():
    modo = request.form.get('modo', 'Agregar')
    rid = request.form.get('id', None)
    registro = ReglaCatalogo.query.get(int(rid)) if rid and rid != '0' else None
    familias = ReglaFamilia.query.filter_by(activo=True).order_by(ReglaFamilia.nombre).all()
    empresas = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('modal-regla-catalogo.html', modo=modo, registro=registro, familias=familias, empresas=empresas)

@regla_bp.route('/catalogo/guardar', methods=['POST'])
def catalogo_guardar():
    rid = request.form.get('id', '').strip()
    familia_id = request.form.get('familia_id', '').strip()
    codigo = request.form.get('codigo', '').strip()
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    rule_type = request.form.get('rule_type', '').strip()
    scope = request.form.get('scope', '').strip()
    field = request.form.get('field', '').strip()
    operator = request.form.get('operator', '').strip()
    params_default_str = request.form.get('params_default', '{}').strip()
    params_editables_str = request.form.get('params_editables', '[]').strip()
    activo = request.form.get('activo') == 'true'

    if not all([familia_id, codigo, nombre, rule_type, scope]):
        return jsonify({'ok': False, 'msg': 'Familia, Código, Nombre, Tipo y Ámbito son obligatorios.'}), 400

    try:
        params_default = json.loads(params_default_str) if params_default_str else {}
        params_editables = json.loads(params_editables_str) if params_editables_str else []
    except json.JSONDecodeError:
        return jsonify({'ok': False, 'msg': 'JSON inválido en parámetros.'}), 400

    try:
        if rid and rid != '0':
            reg = ReglaCatalogo.query.get_or_404(int(rid))
            reg.familia_id = int(familia_id)
            reg.codigo = codigo
            reg.nombre = nombre
            reg.descripcion = descripcion
            reg.rule_type = rule_type
            reg.scope = scope
            reg.field = field or None
            reg.operator = operator or None
            reg.params_default = params_default
            reg.params_editables = params_editables
            reg.activo = activo
            msg = f'Regla "{nombre}" actualizada.'
        else:
            if ReglaCatalogo.query.filter_by(codigo=codigo).first():
                return jsonify({'ok': False, 'msg': f'Ya existe una regla con el código "{codigo}".'}), 400
            reg = ReglaCatalogo(
                familia_id=int(familia_id),
                codigo=codigo, nombre=nombre, descripcion=descripcion,
                rule_type=rule_type, scope=scope,
                field=field or None, operator=operator or None,
                params_default=params_default,
                params_editables=params_editables,
                activo=activo,
            )
            db.session.add(reg)
            msg = f'Regla "{nombre}" creada.'
        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@regla_bp.route('/catalogo/toggle', methods=['POST'])
def catalogo_toggle():
    rid = request.form.get('id', '').strip()
    reg = ReglaCatalogo.query.get_or_404(int(rid))
    reg.activo = not reg.activo
    db.session.commit()
    estado = 'activada' if reg.activo else 'desactivada'
    return jsonify({'ok': True, 'msg': f'Regla {estado}.', 'activo': reg.activo})

@regla_bp.route('/catalogo/asignar', methods=['POST'])
def catalogo_asignar():
    regla_id = request.form.get('regla_id', '').strip()
    empresa_id = request.form.get('empresa_id', '').strip()
    if not regla_id or not empresa_id:
        return jsonify({'ok': False, 'msg': 'Regla y empresa son obligatorios.'}), 400
    regla = ReglaCatalogo.query.get_or_404(int(regla_id))
    existente = ReglaEmpresa.query.filter_by(
        regla_catalogo_id=int(regla_id), empresa_id=int(empresa_id)
    ).first()
    if existente:
        return jsonify({'ok': False, 'msg': 'Esta regla ya está asignada a esa empresa.'}), 400
    try:
        asign = ReglaEmpresa(
            regla_catalogo_id=int(regla_id),
            empresa_id=int(empresa_id),
            params=dict(regla.params_default) if regla.params_default else {},
            is_enabled=True,
        )
        db.session.add(asign)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Regla asignada a la empresa.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500


# ─── REGLAS POR EMPRESA (vista cliente/admin) ─────────────────────────────────

@regla_bp.route('/empresa')
def empresa_view():
    empresa_id = request.args.get('empresa_id', '0')
    empresas = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    query = ReglaEmpresa.query
    if empresa_id != '0':
        query = query.filter_by(empresa_id=int(empresa_id))
    registros = query.all()
    return render_template('reglas-empresa.html',
                           registros=registros,
                           empresas=empresas,
                           empresa_id_sel=int(empresa_id))

@regla_bp.route('/empresa/tabla')
def empresa_tabla():
    empresa_id = request.args.get('empresa_id', '0')
    query = ReglaEmpresa.query
    if empresa_id != '0':
        query = query.filter_by(empresa_id=int(empresa_id))
    registros = query.all()
    return render_template('partials/regla_empresa_rows.html', registros=registros)

@regla_bp.route('/empresa/modal', methods=['POST'])
def empresa_modal():
    modo = request.form.get('modo', 'Editar')
    rid = request.form.get('id', None)
    registro = ReglaEmpresa.query.get(int(rid)) if rid and rid != '0' else None
    return render_template('modal-regla-empresa.html', modo=modo, registro=registro)

@regla_bp.route('/empresa/guardar', methods=['POST'])
def empresa_guardar():
    rid = request.form.get('id', '').strip()
    is_enabled = request.form.get('is_enabled') == 'true'
    params_str = request.form.get('params', '{}').strip()
    reg = ReglaEmpresa.query.get_or_404(int(rid))
    try:
        new_params = json.loads(params_str) if params_str else {}
    except json.JSONDecodeError:
        return jsonify({'ok': False, 'msg': 'JSON inválido en parámetros.'}), 400
    editables = reg.catalogo.params_editables or []
    current = dict(reg.params) if reg.params else {}
    for key in editables:
        if key in new_params:
            current[key] = new_params[key]
    reg.params = current
    reg.is_enabled = is_enabled
    reg.actualizado_en = datetime.utcnow()
    try:
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Configuración actualizada.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@regla_bp.route('/empresa/toggle', methods=['POST'])
def empresa_toggle():
    rid = request.form.get('id', '').strip()
    reg = ReglaEmpresa.query.get_or_404(int(rid))
    reg.is_enabled = not reg.is_enabled
    db.session.commit()
    estado = 'activada' if reg.is_enabled else 'desactivada'
    return jsonify({'ok': True, 'msg': f'Regla {estado}.', 'enabled': reg.is_enabled})

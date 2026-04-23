from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Regla

regla_bp = Blueprint('regla', __name__, url_prefix='/reglas')

@regla_bp.route('/')
def index():
    """Página completa: renderiza tabla con todos los registros."""
    registros = Regla.query.order_by(Regla.id).all()
    return render_template('reglas.html', registros=registros)

@regla_bp.route('/tabla')
def tabla():
    """Solo el <tbody> para HTMX partial refresh (no recarga la página)."""
    registros = Regla.query.order_by(Regla.id).all()
    return render_template('partials/regla_rows.html', registros=registros)

@regla_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal YA relleno con datos de la BD."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Regla.query.get_or_404(int(registro_id))
    return render_template('modal-regla.html', modo=modo, registro=registro)

@regla_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza en PostgreSQL."""
    registro_id = request.form.get('id', '').strip()
    codigo = request.form.get('codigo', '').strip()
    nombre = request.form.get('nombre', '').strip()
    familia = request.form.get('familia', '').strip()
    tipo_regla = request.form.get('tipo_regla', '').strip()
    scope = request.form.get('scope', '').strip()
    campo = request.form.get('campo', '').strip()
    operador = request.form.get('operador', '').strip()
    
    if not codigo or not nombre or not familia or not tipo_regla or not scope:
        return jsonify({'ok': False, 'msg': 'Campos obligatorios faltantes.'}), 400

    if registro_id and registro_id != '0':
        registro = Regla.query.get_or_404(int(registro_id))
        registro.codigo = codigo
        registro.nombre = nombre
        registro.familia = familia
        registro.tipo_regla = tipo_regla
        registro.scope = scope
        registro.campo = campo
        registro.operador = operador
        msg = f'Regla "{nombre}" actualizada con éxito.'
    else:
        registro = Regla(
            codigo=codigo, 
            nombre=nombre,
            familia=familia,
            tipo_regla=tipo_regla,
            scope=scope,
            campo=campo,
            operador=operador,
            params_base={}
        )
        db.session.add(registro)
        msg = f'Regla "{nombre}" creada con éxito.'

    db.session.commit()
    return jsonify({'ok': True, 'msg': msg})

@regla_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Eliminación lógica (activo = False)."""
    registro_id = request.form.get('id', '').strip()
    registro = Regla.query.get_or_404(int(registro_id))
    registro.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Regla "{registro.nombre}" desactivada.'})

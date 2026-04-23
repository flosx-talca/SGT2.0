from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import ReglaEmpresa, Empresa, Regla

regla_empresa_bp = Blueprint('regla_empresa', __name__, url_prefix='/reglas_empresa')

@regla_empresa_bp.route('/')
def index():
    """Página completa: renderiza tabla con todos los registros."""
    registros = ReglaEmpresa.query.order_by(ReglaEmpresa.id).all()
    return render_template('reglas_empresa.html', registros=registros)

@regla_empresa_bp.route('/tabla')
def tabla():
    """Solo el <tbody> para HTMX partial refresh (no recarga la página)."""
    registros = ReglaEmpresa.query.order_by(ReglaEmpresa.id).all()
    return render_template('partials/regla_empresa_rows.html', registros=registros)

@regla_empresa_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal YA relleno con datos de la BD."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = ReglaEmpresa.query.get_or_404(int(registro_id))
    empresas = Empresa.query.filter_by(activo=True).all()
    reglas = Regla.query.filter_by(activo=True).all()
    return render_template('modal-regla-empresa.html', modo=modo, registro=registro, empresas=empresas, reglas=reglas)

@regla_empresa_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza en PostgreSQL."""
    registro_id = request.form.get('id', '').strip()
    empresa_id = request.form.get('empresa_id', '').strip()
    regla_id = request.form.get('regla_id', '').strip()
    
    if not empresa_id or not regla_id:
        return jsonify({'ok': False, 'msg': 'Empresa y Regla son obligatorios.'}), 400

    if registro_id and registro_id != '0':
        registro = ReglaEmpresa.query.get_or_404(int(registro_id))
        registro.empresa_id = empresa_id
        registro.regla_id = regla_id
        msg = f'Asignación actualizada con éxito.'
    else:
        registro = ReglaEmpresa(
            empresa_id=empresa_id,
            regla_id=regla_id,
            params_custom={}
        )
        db.session.add(registro)
        msg = f'Asignación creada con éxito.'

    db.session.commit()
    return jsonify({'ok': True, 'msg': msg})

@regla_empresa_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Eliminación lógica (activo = False)."""
    registro_id = request.form.get('id', '').strip()
    registro = ReglaEmpresa.query.get_or_404(int(registro_id))
    registro.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Asignación desactivada.'})

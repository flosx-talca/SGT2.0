from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import TipoAusencia, Empresa
from datetime import datetime

tipo_ausencia_bp = Blueprint('tipo_ausencia', __name__, url_prefix='/tipos-ausencia')

@tipo_ausencia_bp.route('/')
def index():
    registros = TipoAusencia.query.order_by(TipoAusencia.nombre).all()
    empresas_filtro = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('tipos_ausencia.html', registros=registros, empresas_filtro=empresas_filtro)

@tipo_ausencia_bp.route('/tabla')
def tabla():
    empresa_id = request.args.get('empresa_id', '0')
    query = TipoAusencia.query
    if empresa_id != '0':
        query = query.filter_by(empresa_id=int(empresa_id))
    registros = query.order_by(TipoAusencia.nombre).all()
    return render_template('partials/tipo_ausencia_cards.html', registros=registros)

@tipo_ausencia_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = TipoAusencia.query.get_or_404(int(registro_id))
    
    empresas = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('modal-tipo-ausencia.html', modo=modo, registro=registro, empresas=empresas)

@tipo_ausencia_bp.route('/guardar', methods=['POST'])
def guardar():
    tid = request.form.get('id', '').strip()
    empresa_id = request.form.get('empresa_id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    abreviacion = request.form.get('abreviacion', '').strip()
    color = request.form.get('color', '#95a5a6').strip()
    activo = request.form.get('activo') == 'true'

    if not empresa_id or not nombre or not abreviacion:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    try:
        if tid and tid != '0':
            ta = TipoAusencia.query.get_or_404(int(tid))
            ta.empresa_id = int(empresa_id)
            ta.nombre = nombre
            ta.abreviacion = abreviacion
            ta.color = color
            ta.activo = activo
            msg = f'Tipo de Ausencia "{nombre}" actualizado.'
        else:
            ta = TipoAusencia(
                empresa_id=int(empresa_id),
                nombre=nombre,
                abreviacion=abreviacion,
                color=color,
                activo=activo
            )
            db.session.add(ta)
            msg = f'Tipo de Ausencia "{nombre}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@tipo_ausencia_bp.route('/eliminar', methods=['POST'])
def eliminar():
    tid = request.form.get('id', '').strip()
    ta = TipoAusencia.query.get_or_404(int(tid))
    ta.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Tipo de Ausencia desactivado.'})

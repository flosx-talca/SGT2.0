from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Empresa, Cliente
from app.models.core import Comuna

empresa_bp = Blueprint('empresa', __name__, url_prefix='/empresas')

@empresa_bp.route('/')
def index():
    registros = Empresa.query.order_by(Empresa.razon_social).all()
    return render_template('empresas.html', registros=registros)

@empresa_bp.route('/tabla')
def tabla():
    registros = Empresa.query.order_by(Empresa.razon_social).all()
    return render_template('partials/empresa_rows.html', registros=registros)

@empresa_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Empresa.query.get_or_404(int(registro_id))
    
    clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all()
    comunas = Comuna.query.filter_by(activo=True).order_by(Comuna.descripcion).all()
    
    return render_template('modal-empresa.html', 
                           modo=modo, 
                           registro=registro, 
                           clientes=clientes, 
                           comunas=comunas)

@empresa_bp.route('/guardar', methods=['POST'])
def guardar():
    eid = request.form.get('id', '').strip()
    rut = request.form.get('rut', '').strip()
    razon_social = request.form.get('razon_social', '').strip()
    cliente_id = request.form.get('cliente_id', '').strip()
    comuna_id = request.form.get('comuna_id', '').strip()
    direccion = request.form.get('direccion', '').strip()
    activo = request.form.get('activo') == 'true'

    if not rut or not razon_social or not cliente_id or not comuna_id:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    try:
        if eid and eid != '0':
            empresa = Empresa.query.get_or_404(int(eid))
            dup = Empresa.query.filter(Empresa.rut == rut, Empresa.id != empresa.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya pertenece a otra empresa.'}), 409
            
            empresa.rut = rut
            empresa.razon_social = razon_social
            empresa.cliente_id = int(cliente_id)
            empresa.comuna_id = int(comuna_id)
            empresa.direccion = direccion
            empresa.activo = activo
            msg = f'Empresa "{razon_social}" actualizada.'
        else:
            if Empresa.query.filter_by(rut=rut).first():
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya está registrado.'}), 409
            
            empresa = Empresa(
                rut=rut,
                razon_social=razon_social,
                cliente_id=int(cliente_id),
                comuna_id=int(comuna_id),
                direccion=direccion,
                activo=activo
            )
            db.session.add(empresa)
            msg = f'Empresa "{razon_social}" creada.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@empresa_bp.route('/eliminar', methods=['POST'])
def eliminar():
    eid = request.form.get('id', '').strip()
    empresa = Empresa.query.get_or_404(int(eid))
    empresa.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Empresa desactivada.'})

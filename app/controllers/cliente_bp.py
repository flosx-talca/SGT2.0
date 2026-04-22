from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Cliente

cliente_bp = Blueprint('cliente', __name__, url_prefix='/clientes')

@cliente_bp.route('/')
def index():
    registros = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('clientes.html', registros=registros)

@cliente_bp.route('/tabla')
def tabla():
    registros = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('partials/cliente_rows.html', registros=registros)

@cliente_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Cliente.query.get_or_404(int(registro_id))
    return render_template('modal-cliente.html', modo=modo, registro=registro)

@cliente_bp.route('/guardar', methods=['POST'])
def guardar():
    cid = request.form.get('id', '').strip()
    rut = request.form.get('rut', '').strip()
    nombre = request.form.get('nombre', '').strip()
    apellidos = request.form.get('apellidos', '').strip()
    email = request.form.get('email', '').strip()
    activo = request.form.get('activo') == 'true'

    if not rut or not nombre or not apellidos or not email:
        return jsonify({'ok': False, 'msg': 'Todos los campos marcados con (*) son obligatorios.'}), 400

    try:
        if cid and cid != '0':
            cliente = Cliente.query.get_or_404(int(cid))
            # Validar RUT único
            dup_rut = Cliente.query.filter(Cliente.rut == rut, Cliente.id != cliente.id).first()
            if dup_rut:
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya está registrado.'}), 409
            
            # Validar Email único
            dup_email = Cliente.query.filter(Cliente.email == email, Cliente.id != cliente.id).first()
            if dup_email:
                return jsonify({'ok': False, 'msg': f'El email {email} ya está registrado.'}), 409

            cliente.rut = rut
            cliente.nombre = nombre
            cliente.apellidos = apellidos
            cliente.email = email
            cliente.activo = activo
            msg = f'Cliente "{nombre} {apellidos}" actualizado.'
        else:
            if Cliente.query.filter_by(rut=rut).first():
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya existe.'}), 409
            if Cliente.query.filter_by(email=email).first():
                return jsonify({'ok': False, 'msg': f'El email {email} ya existe.'}), 409
            
            cliente = Cliente(rut=rut, nombre=nombre, apellidos=apellidos, email=email, activo=activo)
            db.session.add(cliente)
            msg = f'Cliente "{nombre} {apellidos}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@cliente_bp.route('/eliminar', methods=['POST'])
def eliminar():
    cid = request.form.get('id', '').strip()
    cliente = Cliente.query.get_or_404(int(cid))
    cliente.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Cliente desactivado.'})

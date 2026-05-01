from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Empresa, Cliente
from app.models.core import Comuna

from flask_login import login_required, current_user

empresa_bp = Blueprint('empresa', __name__, url_prefix='/empresas')

@empresa_bp.route('/')
@login_required
def index():
    if current_user.is_super_admin:
        registros = Empresa.query.order_by(Empresa.razon_social).all()
    elif current_user.is_cliente:
        registros = Empresa.query.filter_by(cliente_id=current_user.cliente_id).order_by(Empresa.razon_social).all()
    else:
        # Administradores normales solo ven sus empresas asignadas
        from app.services.context import get_empresas_usuario
        registros = get_empresas_usuario()
        
    return render_template('empresas.html', registros=registros)

@empresa_bp.route('/tabla')
@login_required
def tabla():
    if current_user.is_super_admin:
        registros = Empresa.query.order_by(Empresa.razon_social).all()
    elif current_user.is_cliente:
        registros = Empresa.query.filter_by(cliente_id=current_user.cliente_id).order_by(Empresa.razon_social).all()
    else:
        from app.services.context import get_empresas_usuario
        registros = get_empresas_usuario()
        
    return render_template('partials/empresa_rows.html', registros=registros)

@empresa_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = db.get_or_404(Empresa, int(registro_id))
    
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
    regimen_exceptuado = request.form.get('regimen_exceptuado') == 'true'

    if not rut or not razon_social or not cliente_id or not comuna_id:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    try:
        if eid and eid != '0':
            empresa = db.get_or_404(Empresa, int(eid))
            dup = Empresa.query.filter(Empresa.rut == rut, Empresa.id != empresa.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya pertenece a otra empresa.'}), 409
            
            empresa.rut = rut
            empresa.razon_social = razon_social
            empresa.cliente_id = int(cliente_id)
            empresa.comuna_id = int(comuna_id)
            empresa.direccion = direccion
            empresa.activo = activo
            empresa.regimen_exceptuado = regimen_exceptuado
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
                activo=activo,
                regimen_exceptuado=regimen_exceptuado
            )
            db.session.add(empresa)
            db.session.flush() # Para obtener el ID
            
            from app.services.empresa_setup import ejecutar_setup_empresa
            ejecutar_setup_empresa(empresa)
            
            msg = f'Empresa "{razon_social}" creada.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@empresa_bp.route('/eliminar', methods=['POST'])
def eliminar():
    eid = request.form.get('id', '').strip()
    empresa = db.get_or_404(Empresa, int(eid))
    empresa.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Empresa desactivada.'})

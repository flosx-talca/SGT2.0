from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.auth import Rol

rol_bp = Blueprint('rol', __name__, url_prefix='/roles')

@rol_bp.route('/')
def index():
    registros = Rol.query.order_by(Rol.descripcion).all()
    return render_template('roles.html', registros=registros)

@rol_bp.route('/tabla')
def tabla():
    registros = Rol.query.order_by(Rol.descripcion).all()
    return render_template('partials/rol_rows.html', registros=registros)

@rol_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Rol.query.get_or_404(int(registro_id))
    return render_template('modal-rol.html', modo=modo, registro=registro)

@rol_bp.route('/guardar', methods=['POST'])
def guardar():
    rid = request.form.get('id', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    activo = request.form.get('activo') == 'true'

    if not descripcion:
        return jsonify({'ok': False, 'msg': 'La descripción es obligatoria.'}), 400

    try:
        if rid and rid != '0':
            rol = Rol.query.get_or_404(int(rid))
            dup = Rol.query.filter(Rol.descripcion == descripcion, Rol.id != rol.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El rol "{descripcion}" ya existe.'}), 409
            
            rol.descripcion = descripcion
            rol.activo = activo
            msg = f'Rol "{descripcion}" actualizado.'
        else:
            if Rol.query.filter_by(descripcion=descripcion).first():
                return jsonify({'ok': False, 'msg': f'El rol "{descripcion}" ya existe.'}), 409
            
            rol = Rol(descripcion=descripcion, activo=activo)
            db.session.add(rol)
            msg = f'Rol "{descripcion}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@rol_bp.route('/eliminar', methods=['POST'])
def eliminar():
    rid = request.form.get('id', '').strip()
    rol = Rol.query.get_or_404(int(rid))
    rol.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Rol desactivado.'})

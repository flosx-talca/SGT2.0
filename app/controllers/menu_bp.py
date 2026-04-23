from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.auth import Menu

menu_bp = Blueprint('menu', __name__, url_prefix='/menus')

@menu_bp.route('/')
def index():
    registros = Menu.query.order_by(Menu.nombre).all()
    return render_template('menus.html', registros=registros)

@menu_bp.route('/tabla')
def tabla():
    registros = Menu.query.order_by(Menu.nombre).all()
    return render_template('partials/menu_rows.html', registros=registros)

@menu_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Menu.query.get_or_404(int(registro_id))
    return render_template('modal-menu.html', modo=modo, registro=registro)

@menu_bp.route('/guardar', methods=['POST'])
def guardar():
    mid = request.form.get('id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    activo = request.form.get('activo') == 'true'

    if not nombre:
        return jsonify({'ok': False, 'msg': 'El nombre del menú es obligatorio.'}), 400

    try:
        if mid and mid != '0':
            menu = Menu.query.get_or_404(int(mid))
            dup = Menu.query.filter(Menu.nombre == nombre, Menu.id != menu.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El menú "{nombre}" ya existe.'}), 409
            
            menu.nombre = nombre
            menu.descripcion = descripcion
            menu.activo = activo
            msg = f'Menú "{nombre}" actualizado.'
        else:
            if Menu.query.filter_by(nombre=nombre).first():
                return jsonify({'ok': False, 'msg': f'El menú "{nombre}" ya existe.'}), 409
            
            menu = Menu(nombre=nombre, descripcion=descripcion, activo=activo)
            db.session.add(menu)
            msg = f'Menú "{nombre}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@menu_bp.route('/eliminar', methods=['POST'])
def eliminar():
    mid = request.form.get('id', '').strip()
    menu = Menu.query.get_or_404(int(mid))
    menu.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Menú desactivado.'})

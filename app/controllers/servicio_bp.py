from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Servicio

servicio_bp = Blueprint('servicio', __name__, url_prefix='/servicios')

@servicio_bp.route('/')
def index():
    registros = Servicio.query.order_by(Servicio.descripcion).all()
    return render_template('servicios.html', registros=registros)

@servicio_bp.route('/tabla')
def tabla():
    registros = Servicio.query.order_by(Servicio.descripcion).all()
    return render_template('partials/servicio_rows.html', registros=registros)

@servicio_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Servicio.query.get_or_404(int(registro_id))
    return render_template('modal-servicio.html', modo=modo, registro=registro)

@servicio_bp.route('/guardar', methods=['POST'])
def guardar():
    sid = request.form.get('id', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    activo = request.form.get('activo') == 'true'

    if not descripcion:
        return jsonify({'ok': False, 'msg': 'La descripción es obligatoria.'}), 400

    try:
        if sid and sid != '0':
            servicio = Servicio.query.get_or_404(int(sid))
            dup = Servicio.query.filter(Servicio.descripcion == descripcion, Servicio.id != servicio.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El servicio "{descripcion}" ya existe.'}), 409
            
            servicio.descripcion = descripcion
            servicio.activo = activo
            msg = f'Servicio "{descripcion}" actualizado.'
        else:
            if Servicio.query.filter_by(descripcion=descripcion).first():
                return jsonify({'ok': False, 'msg': f'El servicio "{descripcion}" ya existe.'}), 409
            
            servicio = Servicio(descripcion=descripcion, activo=activo)
            db.session.add(servicio)
            msg = f'Servicio "{descripcion}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@servicio_bp.route('/eliminar', methods=['POST'])
def eliminar():
    sid = request.form.get('id', '').strip()
    servicio = Servicio.query.get_or_404(int(sid))
    servicio.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Servicio desactivado.'})

from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.core import Feriado, Region
from datetime import datetime

feriado_bp = Blueprint('feriado', __name__, url_prefix='/feriados')

@feriado_bp.route('/')
def index():
    """Página principal de feriados."""
    registros = Feriado.query.order_by(Feriado.fecha.desc()).all()
    return render_template('feriados.html', registros=registros)

@feriado_bp.route('/tabla')
def tabla():
    """Partial refresh de la tabla."""
    registros = Feriado.query.order_by(Feriado.fecha.desc()).all()
    return render_template('partials/feriado_rows.html', registros=registros)

@feriado_bp.route('/modal', methods=['POST'])
def modal():
    """Carga el modal de feriado."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Feriado.query.get_or_404(int(registro_id))
    
    regiones = Region.query.filter_by(activo=True).order_by(Region.descripcion).all()
    return render_template('modal-feriado.html', modo=modo, registro=registro, regiones=regiones)

@feriado_bp.route('/guardar', methods=['POST'])
def guardar():
    """Guarda o actualiza un feriado."""
    feriado_id  = request.form.get('id', '').strip()
    fecha_str   = request.form.get('fecha', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    es_regional = request.form.get('es_regional') == 'true'
    region_id   = request.form.get('region_id', '').strip()
    activo      = request.form.get('activo') == 'true'

    if not fecha_str or not descripcion:
        return jsonify({'ok': False, 'msg': 'Fecha y Descripción son obligatorios.'}), 400

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        rid = int(region_id) if region_id and es_regional else None

        if feriado_id and feriado_id != '0':
            feriado = Feriado.query.get_or_404(int(feriado_id))
            # Validar duplicado
            dup = Feriado.query.filter(Feriado.fecha == fecha, Feriado.id != feriado.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'La fecha {fecha_str} ya está registrada.'}), 409
            
            feriado.fecha = fecha
            feriado.descripcion = descripcion
            feriado.es_regional = es_regional
            feriado.region_id = rid
            feriado.activo = activo
            msg = f'Feriado "{descripcion}" actualizado.'
        else:
            if Feriado.query.filter_by(fecha=fecha).first():
                return jsonify({'ok': False, 'msg': f'La fecha {fecha_str} ya es un feriado.'}), 409
            
            feriado = Feriado(
                fecha=fecha, 
                descripcion=descripcion,
                es_regional=es_regional,
                region_id=rid,
                activo=activo
            )
            db.session.add(feriado)
            msg = f'Feriado "{descripcion}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

@feriado_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Desactiva un feriado."""
    feriado_id = request.form.get('id', '').strip()
    feriado = Feriado.query.get_or_404(int(feriado_id))
    feriado.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Feriado desactivado.'})

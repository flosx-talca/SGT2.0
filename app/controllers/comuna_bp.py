from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.core import Comuna, Region

comuna_bp = Blueprint('comuna', __name__, url_prefix='/comunas')

@comuna_bp.route('/')
def index():
    """Página completa: renderiza tabla con todos los registros."""
    registros = Comuna.query.order_by(Comuna.descripcion).all()
    return render_template('comunas.html', registros=registros)

@comuna_bp.route('/tabla')
def tabla():
    """Solo el <tbody> para HTMX partial refresh."""
    registros = Comuna.query.order_by(Comuna.descripcion).all()
    return render_template('partials/comuna_rows.html', registros=registros)

@comuna_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal relleno con datos de la BD."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    
    if registro_id and registro_id != '0':
        registro = Comuna.query.get_or_404(int(registro_id))
    
    # Necesitamos las regiones para el select del formulario
    regiones = Region.query.filter_by(activo=True).order_by(Region.descripcion).all()
    
    return render_template('modal-comuna.html', modo=modo, registro=registro, regiones=regiones)

@comuna_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza una comuna en PostgreSQL."""
    comuna_id   = request.form.get('id', '').strip()
    codigo      = request.form.get('codigo', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    region_id   = request.form.get('region_id', '').strip()
    activo      = request.form.get('activo') == 'true'

    if not codigo or not descripcion or not region_id:
        return jsonify({'ok': False, 'msg': 'Todos los campos marcados con (*) son obligatorios.'}), 400

    try:
        if comuna_id and comuna_id != '0':
            # ── Editar ──
            comuna = Comuna.query.get_or_404(int(comuna_id))
            # Validar código único (excluyendo la actual)
            dup = Comuna.query.filter(Comuna.codigo == codigo, Comuna.id != comuna.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El código "{codigo}" ya está en uso.'}), 409
            
            comuna.codigo = codigo
            comuna.descripcion = descripcion
            comuna.region_id = int(region_id)
            comuna.activo = activo
            msg = f'Comuna "{descripcion}" actualizada con éxito.'
        else:
            # ── Crear ──
            if Comuna.query.filter_by(codigo=codigo).first():
                return jsonify({'ok': False, 'msg': f'El código "{codigo}" ya existe.'}), 409
            
            comuna = Comuna(
                codigo=codigo,
                descripcion=descripcion,
                region_id=int(region_id),
                activo=activo
            )
            db.session.add(comuna)
            msg = f'Comuna "{descripcion}" creada con éxito.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error en el servidor: {str(e)}'}), 500

@comuna_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Eliminación lógica (activo = False)."""
    registro_id = request.form.get('id', '').strip()
    if not registro_id:
        return jsonify({'ok': False, 'msg': 'ID no proporcionado.'}), 400
        
    try:
        registro = Comuna.query.get_or_404(int(registro_id))
        registro.activo = False
        db.session.commit()
        return jsonify({'ok': True, 'msg': f'Comuna "{registro.descripcion}" desactivada.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error al eliminar: {str(e)}'}), 500

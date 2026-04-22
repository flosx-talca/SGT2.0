from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.core import Region

region_bp = Blueprint('region', __name__, url_prefix='/regiones')


@region_bp.route('/')
def index():
    """Lista todas las regiones, renderiza la tabla completa."""
    regiones = Region.query.order_by(Region.codigo).all()
    return render_template('regiones.html', regiones=regiones)


@region_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal ya relleno con datos de la BD."""
    modo = request.form.get('modo', 'Agregar')
    region_id = request.form.get('id', None)
    region = None
    if region_id and region_id != '0':
        region = Region.query.get_or_404(int(region_id))
    return render_template('modal-region.html', modo=modo, region=region)


@region_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza una región en PostgreSQL."""
    region_id  = request.form.get('id', '').strip()
    codigo     = request.form.get('codigo', '').strip().upper()
    descripcion = request.form.get('descripcion', '').strip()
    activo     = request.form.get('activo') == 'true'

    if not codigo or not descripcion:
        return jsonify({'ok': False, 'msg': 'Código y Descripción son obligatorios.'}), 400

    if region_id and region_id != '0':
        # ── Editar ──
        region = Region.query.get_or_404(int(region_id))
        # Validar que el código no esté tomado por otra región
        dup = Region.query.filter(Region.codigo == codigo, Region.id != region.id).first()
        if dup:
            return jsonify({'ok': False, 'msg': f'El código "{codigo}" ya está en uso.'}), 409
        region.codigo      = codigo
        region.descripcion = descripcion
        region.activo      = activo
        msg = f'Región "{descripcion}" actualizada con éxito.'
    else:
        # ── Crear ──
        if Region.query.filter_by(codigo=codigo).first():
            return jsonify({'ok': False, 'msg': f'El código "{codigo}" ya existe.'}), 409
        region = Region(codigo=codigo, descripcion=descripcion, activo=activo)
        db.session.add(region)
        msg = f'Región "{descripcion}" creada con éxito.'

    db.session.commit()
    return jsonify({'ok': True, 'msg': msg})


@region_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Elimina lógicamente una región (activo = False)."""
    region_id = request.form.get('id', '').strip()
    if not region_id:
        return jsonify({'ok': False, 'msg': 'ID no proporcionado.'}), 400

    region = Region.query.get_or_404(int(region_id))
    region.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Región "{region.descripcion}" desactivada.'})

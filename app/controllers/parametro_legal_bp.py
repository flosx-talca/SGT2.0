from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import ParametroLegal

parametro_legal_bp = Blueprint('parametro_legal', __name__, url_prefix='/parametros_legales')

@parametro_legal_bp.route('/')
def index():
    """Página principal del mantenedor."""
    parametros = ParametroLegal.query.order_by(ParametroLegal.categoria, ParametroLegal.codigo).all()
    return render_template('parametros_legales/index.html', parametros=parametros)

@parametro_legal_bp.route('/tabla')
def tabla():
    """Partial para recarga HTMX de la tabla."""
    parametros = ParametroLegal.query.order_by(ParametroLegal.categoria, ParametroLegal.codigo).all()
    return render_template('parametros_legales/partials/table_rows.html', parametros=parametros)

@parametro_legal_bp.route('/modal', methods=['POST'])
def modal():
    """Devuelve el HTML del modal para crear o editar."""
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = ParametroLegal.query.get_or_404(int(registro_id))
    
    # Obtener categorías únicas existentes para el datalist o select
    categorias = db.session.query(ParametroLegal.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    
    return render_template('parametros_legales/modal.html', 
                           modo=modo, 
                           registro=registro, 
                           categorias=categorias)

@parametro_legal_bp.route('/guardar', methods=['POST'])
def guardar():
    """Crea o actualiza un parámetro legal."""
    pid = request.form.get('id', '').strip()
    codigo = request.form.get('codigo', '').strip().upper()
    valor = request.form.get('valor', '').strip()
    categoria = request.form.get('categoria', 'General').strip()
    descripcion = request.form.get('descripcion', '').strip()
    es_obligatorio = request.form.get('es_obligatorio') == 'true'
    es_activo = request.form.get('es_activo') == 'true'

    if not codigo or not valor:
        return jsonify({'ok': False, 'msg': 'Código y Valor son obligatorios.'}), 400

    try:
        if pid and pid != '0':
            param = ParametroLegal.query.get_or_404(int(pid))
            # Verificar duplicado de código
            dup = ParametroLegal.query.filter(ParametroLegal.codigo == codigo, ParametroLegal.id != param.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El código {codigo} ya está en uso.'}), 409
            
            param.codigo = codigo
            param.valor = valor
            param.categoria = categoria
            param.descripcion = descripcion
            param.es_obligatorio = es_obligatorio
            param.es_activo = es_activo
            msg = f'Parámetro {codigo} actualizado.'
        else:
            if ParametroLegal.query.filter_by(codigo=codigo).first():
                return jsonify({'ok': False, 'msg': f'El código {codigo} ya existe.'}), 409
            
            param = ParametroLegal(
                codigo=codigo,
                valor=valor,
                categoria=categoria,
                descripcion=descripcion,
                es_obligatorio=es_obligatorio,
                es_activo=es_activo
            )
            db.session.add(param)
            msg = f'Parámetro {codigo} creado.'
            
        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@parametro_legal_bp.route('/toggle/<int:id>', methods=['POST'])
def toggle(id):
    """Activa/Desactiva rápidamente un parámetro."""
    param = ParametroLegal.query.get_or_404(id)
    param.es_activo = not param.es_activo
    db.session.commit()
    return jsonify({'ok': True, 'es_activo': param.es_activo})

@parametro_legal_bp.route('/eliminar', methods=['POST'])
def eliminar():
    """Eliminación lógica."""
    pid = request.form.get('id', '').strip()
    param = ParametroLegal.query.get_or_404(int(pid))
    param.es_activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Parámetro {param.codigo} desactivado.'})

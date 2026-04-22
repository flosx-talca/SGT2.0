from flask import Blueprint, render_template, request

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/planificacion')
def planificacion():
    return render_template('simulacion.html')

@main_bp.route('/simulacion')
def simulacion():
    return render_template('simulacion.html')

# Endpoints para modales genéricos (retornan HTML parcial)
@main_bp.route('/modal-<name>', methods=['POST'])
def render_modal(name):
    modo = request.form.get('modo', '')
    id_item = request.form.get('id', '')
    template_name = f'modal-{name}.html'
    try:
        return render_template(template_name, modo=modo, id=id_item)
    except Exception:
        return f"<div class='alert alert-danger'>Modal no encontrado: {template_name}</div>", 404

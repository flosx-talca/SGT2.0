from flask import Blueprint, render_template, request

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/trabajadores')
def trabajadores():
    return render_template('trabajadores.html')

@main_bp.route('/turnos')
def turnos():
    return render_template('turnos.html')

@main_bp.route('/planificacion')
def planificacion():
    return render_template('simulacion.html') 

@main_bp.route('/reglas-empresa')
def reglas_empresa():
    return render_template('reglas-empresa.html')

@main_bp.route('/clientes')
def clientes():
    return render_template('clientes.html')

@main_bp.route('/usuarios')
def usuarios():
    return render_template('usuarios.html')

@main_bp.route('/empresas')
def empresas():
    return render_template('empresas.html')

@main_bp.route('/servicios')
def servicios():
    return render_template('servicios.html')

@main_bp.route('/reglas-familias')
def reglas_familias():
    return render_template('reglas-familias.html')

@main_bp.route('/reglas-config')
def reglas_config():
    return render_template('reglas-config.html')

@main_bp.route('/simulacion')
def simulacion():
    return render_template('simulacion.html')

@main_bp.route('/reglas')
def reglas():
    return render_template('reglas.html')


@main_bp.route('/comunas')
def comunas():
    return render_template('comunas.html')

@main_bp.route('/feriados')
def feriados():
    return render_template('feriados.html')

@main_bp.route('/roles')
def roles():
    return render_template('roles.html')

@main_bp.route('/menus')
def menus():
    return render_template('menus.html')

# Endpoints para modales (retornan HTML parcial)
@main_bp.route('/modal-<name>', methods=['POST'])
def render_modal(name):
    modo = request.form.get('modo', '')
    id_item = request.form.get('id', '')
    template_name = f'modal-{name}.html'
    try:
        return render_template(template_name, modo=modo, id=id_item)
    except Exception as e:
        return f"<div class='alert alert-danger'>Modal no encontrado: {template_name}</div>", 404

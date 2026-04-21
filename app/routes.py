from flask import render_template, request, jsonify

def init_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login():
        return render_template('login.html')

    @app.route('/trabajadores')
    def trabajadores():
        return render_template('trabajadores.html')

    @app.route('/turnos')
    def turnos():
        return render_template('turnos.html')

    @app.route('/planificacion')
    def planificacion():
        # TODO: si no hay planificacion.html, quizás redirige o tiene otro nombre
        return render_template('simulacion.html') 

    @app.route('/reglas-empresa')
    def reglas_empresa():
        return render_template('reglas-empresa.html')

    @app.route('/clientes')
    def clientes():
        return render_template('clientes.html')

    @app.route('/empresas')
    def empresas():
        return render_template('empresas.html')

    @app.route('/servicios')
    def servicios():
        return render_template('servicios.html')

    @app.route('/reglas-familias')
    def reglas_familias():
        return render_template('reglas-familias.html')

    @app.route('/reglas-config')
    def reglas_config():
        return render_template('reglas-config.html')

    @app.route('/simulacion')
    def simulacion():
        return render_template('simulacion.html')

    @app.route('/reglas')
    def reglas():
        return render_template('reglas.html')

    # Endpoints para modales (retornan HTML parcial)
    @app.route('/modal-<name>', methods=['POST'])
    def render_modal(name):
        modo = request.form.get('modo', '')
        id_item = request.form.get('id', '')
        template_name = f'modal-{name}.html'
        try:
            return render_template(template_name, modo=modo, id=id_item)
        except Exception as e:
            return f"<div class='alert alert-danger'>Modal no encontrado: {template_name}</div>", 404

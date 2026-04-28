from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from app.models.business import Servicio, Turno, TipoAusencia, Empresa, Trabajador
from app.services.context import get_empresa_activa_id
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    empresa_id = get_empresa_activa_id()
    if empresa_id:
        total_trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).count()
        total_empresas = 1
    else:
        total_trabajadores = Trabajador.query.filter_by(activo=True).count()
        total_empresas = Empresa.query.filter_by(activo=True).count()

    return render_template('index.html', 
                           total_trabajadores=total_trabajadores, 
                           total_empresas=total_empresas)

@main_bp.route('/planificacion')
@login_required
def planificacion():
    empresa_id = get_empresa_activa_id()
    if not empresa_id:
        if current_user.rol.descripcion == 'Super Admin':
            # Super Admin puede entrar pero deberá elegir empresa en el UI
            pass
        else:
            return render_template('auth/select_company.html')

    if empresa_id:
        servicios = Servicio.query.join(Servicio.empresas_asociadas).filter(Empresa.id == empresa_id, Servicio.activo == True).all()
        turnos = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    else:
        servicios = []
        turnos = []
    tipos_ausencia = TipoAusencia.query.filter_by(empresa_id=empresa_id, activo=True).all()
    now = datetime.now()
    return render_template('simulacion.html', 
                           servicios=servicios, 
                           turnos=turnos, 
                           tipos_ausencia=tipos_ausencia, 
                           current_year=now.year, 
                           current_month=now.month)

@main_bp.route('/simulacion')
@login_required
def simulacion():
    return planificacion()

@main_bp.route('/modal-<name>', methods=['POST'])
@login_required
def render_modal(name):
    modo = request.form.get('modo', '')
    id_item = request.form.get('id', '')
    template_name = f'modal-{name}.html'
    try:
        return render_template(template_name, modo=modo, id=id_item)
    except Exception as e:
        return f"<div class='alert alert-danger'>Modal no encontrado: {template_name}</div>", 404

@main_bp.route('/reglas_familias')
@login_required
def reglas_familias():
    # Placeholder para evitar BuildError
    from flask import redirect, url_for
    return redirect(url_for('regla_empresa.index'))

@main_bp.route('/reglas_config')
@login_required
def reglas_config():
    # Placeholder para evitar BuildError
    from flask import redirect, url_for
    return redirect(url_for('regla.index'))

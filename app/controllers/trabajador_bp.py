from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Trabajador, Empresa, Servicio, Turno, TrabajadorPreferencia, TrabajadorAusencia, TipoAusencia

trabajador_bp = Blueprint('trabajador', __name__, url_prefix='/trabajadores')

JORNADA_DEFAULT = 42  # horas semanales por defecto (jornada estándar Chile)

@trabajador_bp.route('/')
def index():
    registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('trabajadores.html', registros=registros)


@trabajador_bp.route('/tabla')
def tabla():
    registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('partials/trabajador_rows.html', registros=registros)


@trabajador_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Trabajador.query.get_or_404(int(registro_id))

    empresas  = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.descripcion).all()

    # Turnos únicos para la tabla de preferencias (por empresa si hay contexto)
    turnos_db = Turno.query.filter_by(activo=True).all()
    tipos_turno = []
    vistos = set()
    for t in turnos_db:
        if t.abreviacion not in vistos:
            tipos_turno.append({'abreviacion': t.abreviacion, 'color': t.color})
            vistos.add(t.abreviacion)

    if not tipos_turno:
        tipos_turno = [
            {'abreviacion': 'M', 'color': '#18bc9c'},
            {'abreviacion': 'T', 'color': '#3498db'},
            {'abreviacion': 'I', 'color': '#f39c12'},
            {'abreviacion': 'N', 'color': '#34495e'}
        ]

    tipos_ausencia = TipoAusencia.query.filter_by(activo=True).all()

    return render_template('modal-trabajador.html',
                           modo=modo,
                           registro=registro,
                           empresas=empresas,
                           servicios=servicios,
                           tipos_turno=tipos_turno,
                           tipos_ausencia=tipos_ausencia,
                           jornada_default=JORNADA_DEFAULT)


@trabajador_bp.route('/guardar', methods=['POST'])
def guardar():
    tid         = request.form.get('id', '').strip()
    rut         = request.form.get('rut', '').strip()
    nombre      = request.form.get('nombre', '').strip()
    apellido1   = request.form.get('apellido1', '').strip()
    apellido2   = request.form.get('apellido2', '').strip()
    empresa_id  = request.form.get('empresa_id', '').strip()
    servicio_id = request.form.get('servicio_id', '').strip()
    cargo       = request.form.get('cargo', '').strip()
    email       = request.form.get('email', '').strip()
    telefono    = request.form.get('telefono', '').strip()
    tipo_contrato = request.form.get('tipo_contrato', 'full-time').strip()
    horas_str   = request.form.get('horas_semanales', '').strip()
    activo      = request.form.get('activo') == 'true'

    if not rut or not nombre or not apellido1 or not empresa_id or not servicio_id:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    # horas_semanales: obligatorio para el builder.
    # Si el usuario no ingresó nada se usa la jornada estándar.
    horas = int(horas_str) if horas_str else JORNADA_DEFAULT

    try:
        if tid and tid != '0':
            trabajador = Trabajador.query.get_or_404(int(tid))
            dup = Trabajador.query.filter(Trabajador.rut == rut, Trabajador.id != trabajador.id).first()
            if dup:
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya existe.'}), 409

            trabajador.rut             = rut
            trabajador.nombre          = nombre
            trabajador.apellido1       = apellido1
            trabajador.apellido2       = apellido2
            trabajador.empresa_id      = int(empresa_id)
            trabajador.servicio_id     = int(servicio_id)
            trabajador.cargo           = cargo
            trabajador.email           = email
            trabajador.telefono        = telefono
            trabajador.tipo_contrato   = tipo_contrato
            trabajador.horas_semanales = horas
            trabajador.activo          = activo
            msg = f'Trabajador "{nombre} {apellido1}" actualizado.'
        else:
            if Trabajador.query.filter_by(rut=rut).first():
                return jsonify({'ok': False, 'msg': f'El RUT {rut} ya existe.'}), 409

            trabajador = Trabajador(
                rut             = rut,
                nombre          = nombre,
                apellido1       = apellido1,
                apellido2       = apellido2,
                empresa_id      = int(empresa_id),
                servicio_id     = int(servicio_id),
                cargo           = cargo,
                email           = email,
                telefono        = telefono,
                tipo_contrato   = tipo_contrato,
                horas_semanales = horas,
                activo          = activo
            )
            db.session.add(trabajador)
            db.session.flush()
            msg = f'Trabajador "{nombre} {apellido1}" creado.'

        # Procesar preferencias de turno por día de semana
        TrabajadorPreferencia.query.filter_by(trabajador_id=trabajador.id).delete()
        for i in range(7):  # 0=Lunes … 6=Domingo
            prefs = request.form.getlist(f'pref_{i}[]')
            for p in prefs:
                db.session.add(TrabajadorPreferencia(
                    trabajador_id=trabajador.id, dia_semana=i, turno=p
                ))

        # Procesar ausencias
        TrabajadorAusencia.query.filter_by(trabajador_id=trabajador.id).delete()
        aus_inis  = request.form.getlist('ausencia_ini[]')
        aus_fins  = request.form.getlist('ausencia_fin[]')
        aus_tipos = request.form.getlist('ausencia_motivo[]')
        for ini, fin, tipo_id in zip(aus_inis, aus_fins, aus_tipos):
            if tipo_id:
                tipo_obj = TipoAusencia.query.get(int(tipo_id))
                db.session.add(TrabajadorAusencia(
                    trabajador_id    = trabajador.id,
                    fecha_inicio     = ini,
                    fecha_fin        = fin,
                    tipo_ausencia_id = int(tipo_id),
                    motivo           = tipo_obj.nombre if tipo_obj else 'Ausencia'
                ))

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500


@trabajador_bp.route('/eliminar', methods=['POST'])
def eliminar():
    tid = request.form.get('id', '').strip()
    trabajador = Trabajador.query.get_or_404(int(tid))
    trabajador.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Trabajador desactivado.'})

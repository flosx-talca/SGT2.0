from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.context import get_empresa_activa_id
from app.database import db
from app.models.business import Trabajador, Empresa, Servicio, Turno, TrabajadorRestriccionTurno, TrabajadorAusencia, TipoAusencia, TipoAusenciaPlantilla
from app.models.enums import RestrictionType, CategoriaAusencia
from datetime import date

trabajador_bp = Blueprint('trabajador', __name__, url_prefix='/trabajadores')

JORNADA_DEFAULT = 42  # horas semanales por defecto (jornada estándar Chile)

@trabajador_bp.route('/')
@login_required
def index():
    emp_id = get_empresa_activa_id()
    if emp_id:
        registros = Trabajador.query.filter_by(empresa_id=emp_id).order_by(Trabajador.nombre).all()
    else:
        registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('trabajadores.html', registros=registros)


@trabajador_bp.route('/tabla')
@login_required
def tabla():
    emp_id = get_empresa_activa_id()
    if emp_id:
        registros = Trabajador.query.filter_by(empresa_id=emp_id).order_by(Trabajador.nombre).all()
    else:
        registros = Trabajador.query.order_by(Trabajador.nombre).all()
    return render_template('partials/trabajador_rows.html', registros=registros)


@trabajador_bp.route('/modal', methods=['POST'])
@login_required
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Trabajador.query.get_or_404(int(registro_id))

    emp_id = get_empresa_activa_id()
    print(f"DEBUG: modal - emp_id={emp_id}, current_user={current_user.nombre}, rol={current_user.rol.descripcion}")
    
    if emp_id:
        empresas  = Empresa.query.filter_by(id=emp_id, activo=True).all()
        servicios = Servicio.query.join(Servicio.empresas_asociadas).filter(Empresa.id == emp_id, Servicio.activo == True).order_by(Servicio.descripcion).all()
        turnos_db = Turno.query.filter_by(empresa_id=emp_id, activo=True).all()
        tipos_ausencia = TipoAusencia.query.filter_by(empresa_id=emp_id, activo=True).all()
    else:
        # Modo Super Admin o Cliente sin empresa seleccionada
        from app.services.context import get_empresas_usuario
        empresas = get_empresas_usuario()
        ids = [e.id for e in empresas]
        print(f"DEBUG: modal - ids_asignados={ids}")
        if ids:
            servicios = Servicio.query.join(Servicio.empresas_asociadas).filter(Empresa.id.in_(ids), Servicio.activo == True).order_by(Servicio.descripcion).all()
            turnos_db = Turno.query.filter(Turno.empresa_id.in_(ids), Turno.activo == True).all()
            tipos_ausencia = TipoAusencia.query.filter(TipoAusencia.empresa_id.in_(ids), TipoAusencia.activo == True).all()
        else:
            servicios = []
            turnos_db = []
            tipos_ausencia = []
    
    print(f"DEBUG: modal - data loaded: empresas={len(empresas)}, servicios={len(servicios)}, turnos={len(turnos_db)}")

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

    return render_template('modal-trabajador.html',
                           modo=modo,
                           registro=registro,
                           empresas=empresas,
                           servicios=servicios,
                           tipos_turno=tipos_turno,
                           tipos_ausencia=tipos_ausencia,
                           jornada_default=JORNADA_DEFAULT)


@trabajador_bp.route('/modal_restriccion', methods=['POST'])
def modal_restriccion():
    trabajador_id = request.form.get('id')
    trabajador = Trabajador.query.get_or_404(int(trabajador_id))
    
    # Obtener turnos de la empresa
    shifts = Turno.query.filter_by(empresa_id=trabajador.empresa_id, activo=True).order_by(Turno.id).all()
    
    # 1. Obtener ausencias globales (Universo)
    tipos_ausencia_global = TipoAusenciaPlantilla.query.filter_by(
        categoria=CategoriaAusencia.AUSENCIA,
        activo=True
    ).order_by(TipoAusenciaPlantilla.nombre).all()

    # 2. Obtener TODAS las ausencias de la empresa (Base + Personalizadas)
    tipos_ausencia_empresa = TipoAusencia.query.filter_by(
        empresa_id=trabajador.empresa_id, 
        categoria=CategoriaAusencia.AUSENCIA,
        activo=True
    ).order_by(TipoAusencia.nombre).all()
    
    # 3. Obtener restricciones universales (Universo / Plantilla)
    tipos_restriccion_global = TipoAusenciaPlantilla.query.filter_by(
        categoria=CategoriaAusencia.RESTRICCION,
        activo=True
    ).order_by(TipoAusenciaPlantilla.nombre).all()
    
    from app.services.legal_engine import LegalEngine
    res_legal = LegalEngine.resumen_legal(trabajador, None, 7)
    
    return render_template('modal-restriccion.html',
                           trabajador=trabajador,
                           shifts=shifts,
                           tipos_ausencia_global=tipos_ausencia_global,
                           tipos_ausencia_empresa=tipos_ausencia_empresa,
                           tipos_restriccion_global=tipos_restriccion_global,
                           res_legal=res_legal)


@trabajador_bp.route('/guardar', methods=['POST'])
@login_required
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
    tipo_contrato = request.form.get('tipo_contrato', 'full_time').strip()
    horas_str   = request.form.get('horas_semanales', '').strip()
    activo      = request.form.get('activo') == 'true'

    if not rut or not nombre or not apellido1 or not empresa_id or not servicio_id:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    # horas_semanales: obligatorio para el builder.
    # Si el usuario no ingresó nada se usa la jornada estándar.
    horas = int(horas_str) if horas_str else JORNADA_DEFAULT
    permite_extra = request.form.get('permite_horas_extra') == 'true'

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
            trabajador.permite_horas_extra = permite_extra
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
                permite_horas_extra = permite_extra,
                activo          = activo
            )
            db.session.add(trabajador)
            db.session.flush()
            msg = f'Trabajador "{nombre} {apellido1}" creado.'

        # Procesar preferencias de turno (migrado a TrabajadorRestriccionTurno patrón 2099)
        # Limpiar patrones permanentes previos para este trabajador
        TrabajadorRestriccionTurno.query.filter_by(
            trabajador_id=trabajador.id, 
            fecha_fin=date(2099, 12, 31)
        ).delete()
        
        for i in range(7):  # 0=Lunes … 6=Domingo
            prefs  = request.form.getlist(f'pref_{i}[]')
            tipo_i_str = request.form.get(f'pref_tipo_{i}', 'preferencia')
            
            # Mapeo de tipos antiguos a nuevos tipos de RestrictionType
            tipo_map = {
                'fijo': RestrictionType.TURNO_FIJO,
                'solo_turno': RestrictionType.SOLO_TURNO,
                'preferencia': RestrictionType.TURNO_PREFERENTE
            }
            tipo_final = tipo_map.get(tipo_i_str, RestrictionType.TURNO_PREFERENTE)
            naturaleza = 'hard' if tipo_final != RestrictionType.TURNO_PREFERENTE else 'soft'
            
            for p_abrev in prefs:
                # Buscar el turno real por su abreviación en la empresa actual
                t_obj = Turno.query.filter_by(abreviacion=p_abrev, empresa_id=trabajador.empresa_id).first()
                if t_obj:
                    db.session.add(TrabajadorRestriccionTurno(
                        trabajador_id=trabajador.id,
                        empresa_id=trabajador.empresa_id,
                        tipo=tipo_final,
                        naturaleza=naturaleza,
                        fecha_inicio=date.today(),
                        fecha_fin=date(2099, 12, 31),
                        dias_semana=[i],
                        turno_id=t_obj.id,
                        activo=True
                    ))

        # Las ausencias ahora se gestionan en ausencia_bp.py
        
        db.session.commit()

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500


@trabajador_bp.route('/eliminar', methods=['POST'])
@login_required
def eliminar():
    tid = request.form.get('id', '').strip()
    trabajador = Trabajador.query.get_or_404(int(tid))
    trabajador.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Trabajador desactivado.'})

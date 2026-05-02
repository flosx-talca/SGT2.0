from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import TurnoPlantilla, TipoAusenciaPlantilla
from app.models.enums import CategoriaAusencia
from flask_login import login_required, current_user
from datetime import datetime

plantillas_bp = Blueprint('plantilla', __name__, url_prefix='/plantillas')

@plantillas_bp.route('/')
@login_required
def index():
    if not current_user.is_super_admin:
        from flask import abort
        abort(403)
    
    turnos = TurnoPlantilla.query.order_by(TurnoPlantilla.nombre).all()
    ausencias = TipoAusenciaPlantilla.query.order_by(TipoAusenciaPlantilla.nombre).all()
    
    return render_template('plantillas/index.html', turnos=turnos, ausencias=ausencias)

# --- TURNOS PLANTILLA ---

@plantillas_bp.route('/turno/tabla')
@login_required
def tabla_turnos():
    turnos = TurnoPlantilla.query.order_by(TurnoPlantilla.nombre).all()
    return render_template('plantillas/partials/turno_rows.html', turnos=turnos)

@plantillas_bp.route('/turno/modal', methods=['POST'])
@login_required
def modal_turno():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id')
    registro = None
    if registro_id and registro_id != '0':
        registro = TurnoPlantilla.query.get_or_404(int(registro_id))
    return render_template('plantillas/modal_turno.html', modo=modo, registro=registro)

@plantillas_bp.route('/turno/guardar', methods=['POST'])
@login_required
def guardar_turno():
    if not current_user.is_super_admin:
        return jsonify({'ok': False, 'msg': 'No tiene permisos.'}), 403

    tid = request.form.get('id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    abreviacion = request.form.get('abreviacion', '').strip()
    h_inicio = request.form.get('hora_inicio', '').strip()
    h_fin = request.form.get('hora_fin', '').strip()
    color = request.form.get('color', '#18bc9c').strip()
    dotacion = request.form.get('dotacion_diaria', '1')
    activo = request.form.get('activo') == 'true'

    try:
        hi = datetime.strptime(h_inicio, '%H:%M').time()
        hf = datetime.strptime(h_fin, '%H:%M').time()
        es_noc = hf <= hi

        if tid and tid != '0':
            t = TurnoPlantilla.query.get_or_404(int(tid))
            t.nombre = nombre
            t.abreviacion = abreviacion
            t.hora_inicio = hi
            t.hora_fin = hf
            t.color = color
            t.dotacion_diaria = int(dotacion)
            t.es_nocturno = es_noc
            t.activo = activo
        else:
            t = TurnoPlantilla(
                nombre=nombre, abreviacion=abreviacion,
                hora_inicio=hi, hora_fin=hf, color=color,
                dotacion_diaria=int(dotacion), es_nocturno=es_noc,
                activo=activo
            )
            db.session.add(t)
        
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Plantilla de turno guardada.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

# --- AUSENCIAS PLANTILLA ---

@plantillas_bp.route('/ausencia/tabla')
@login_required
def tabla_ausencias():
    ausencias = TipoAusenciaPlantilla.query.order_by(TipoAusenciaPlantilla.nombre).all()
    return render_template('plantillas/partials/ausencia_rows.html', ausencias=ausencias)

@plantillas_bp.route('/ausencia/modal', methods=['POST'])
@login_required
def modal_ausencia():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id')
    registro = None
    if registro_id and registro_id != '0':
        registro = TipoAusenciaPlantilla.query.get_or_404(int(registro_id))
    
    categorias = [c.value for c in CategoriaAusencia]
    return render_template('plantillas/modal_ausencia.html', modo=modo, registro=registro, categorias=categorias)

@plantillas_bp.route('/ausencia/guardar', methods=['POST'])
@login_required
def guardar_ausencia():
    if not current_user.is_super_admin:
        return jsonify({'ok': False, 'msg': 'No tiene permisos.'}), 403

    aid = request.form.get('id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    abreviacion = request.form.get('abreviacion', '').strip()
    color = request.form.get('color', '#95a5a6').strip()
    categoria = request.form.get('categoria')
    tipo_rest = request.form.get('tipo_restriccion', '').strip()
    activo = request.form.get('activo') == 'true'

    try:
        if aid and aid != '0':
            a = TipoAusenciaPlantilla.query.get_or_404(int(aid))
            a.nombre = nombre
            a.abreviacion = abreviacion
            a.color = color
            a.categoria = CategoriaAusencia(categoria)
            a.tipo_restriccion = tipo_rest if tipo_rest else None
            a.activo = activo
        else:
            a = TipoAusenciaPlantilla(
                nombre=nombre, abreviacion=abreviacion,
                color=color, categoria=CategoriaAusencia(categoria),
                tipo_restriccion=tipo_rest if tipo_rest else None,
                activo=activo
            )
            db.session.add(a)
        
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Plantilla de ausencia guardada.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

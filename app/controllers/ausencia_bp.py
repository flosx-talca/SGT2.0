from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.services.context import get_empresa_activa_id
from app.database import db
from app.models.business import Trabajador, TrabajadorAusencia, TipoAusencia, Turno, TrabajadorRestriccionTurno
from app.models.enums import CategoriaAusencia
from app.services.capacidad_service import calcular_capacidad_detallada
from datetime import date, datetime

ausencia_bp = Blueprint('ausencia', __name__)

@ausencia_bp.route('/ausencias')
@login_required
def index():
    empresa_id = get_empresa_activa_id()
    mes = int(request.args.get('mes', date.today().month))
    anio = int(request.args.get('anio', date.today().year))
    
    # Si hay empresa activa, filtramos. Si no (Super Admin), vemos todo.
    if empresa_id:
        ausencias = TrabajadorAusencia.query.join(Trabajador).filter(
            Trabajador.empresa_id == empresa_id
        ).order_by(TrabajadorAusencia.fecha_inicio.desc()).all()
        capacidad = calcular_capacidad_detallada(empresa_id, mes, anio)
        trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Trabajador.nombre).all()
        tipos = TipoAusencia.query.filter_by(empresa_id=empresa_id, activo=True).all()
    else:
        ausencias = TrabajadorAusencia.query.order_by(TrabajadorAusencia.fecha_inicio.desc()).all()
        capacidad = {'estado': 'ok', 'mensaje': 'Seleccione una empresa para ver el análisis de capacidad.', 'dias_con_problema': []}
        trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()
        tipos = TipoAusencia.query.filter_by(activo=True).all()
    
    return render_template('ausencias.html',
                           ausencias=ausencias,
                           capacidad=capacidad,
                           trabajadores=trabajadores,
                           tipos=tipos,
                           mes_act=mes, 
                           anio_act=anio)

@ausencia_bp.route('/ausencias/modal')
@ausencia_bp.route('/ausencias/modal/<int:id>')
@login_required
def modal_nueva(id=None):
    ausencia = None
    if id:
        ausencia = TrabajadorAusencia.query.get_or_404(id)
        
    empresa_id = get_empresa_activa_id()
    if not empresa_id:
        return "Seleccione una empresa primero", 400

    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Trabajador.nombre).all()
    tipos = TipoAusencia.query.filter_by(empresa_id=empresa_id, activo=True).all()
    turnos = Turno.query.filter_by(empresa_id=empresa_id, activo=True).all()
    
    return render_template('modal-ausencia.html', 
                           trabajadores=trabajadores, 
                           tipos=tipos, 
                           turnos=turnos,
                           ausencia=ausencia,
                           CategoriaAusencia=CategoriaAusencia)

@ausencia_bp.route('/ausencias/impacto', methods=['POST'])
@login_required
def impacto():
    data = request.get_json()
    tid = data.get('trabajador_id')
    inicio_str = data.get('fecha_inicio')
    fin_str = data.get('fecha_fin')
    exclude_id = data.get('exclude_id')
    
    if not all([tid, inicio_str, fin_str]):
        return jsonify({'estado': 'ok', 'mensaje': 'Complete fechas para evaluar.'})

    try:
        inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date()
        fin = datetime.strptime(fin_str, '%Y-%m-%d').date()
    except:
        return jsonify({'estado': 'error', 'mensaje': 'Fechas inválidas'})

    trabajador = Trabajador.query.get(int(tid))
    if not trabajador:
        return jsonify({'estado': 'error', 'mensaje': 'Trabajador no encontrado'})
        
    # Calcular impacto inyectando la nueva ausencia potencial al cálculo
    # Si estamos editando (exclude_id), el servicio debe ignorar la versión antigua
    resultado = calcular_capacidad_detallada(
        trabajador.empresa_id, inicio.month, inicio.year,
        ausencias_temporales=[{
            'trabajador_id': trabajador.id,
            'fecha_inicio': inicio,
            'fecha_fin': fin
        }],
        exclude_ausencia_id=int(exclude_id) if exclude_id and exclude_id != '0' else None
    )
    return jsonify(resultado)

@ausencia_bp.route('/ausencias/guardar', methods=['POST'])
@login_required
def guardar():
    aid = request.form.get('id')
    tid = request.form.get('trabajador_id')
    tipo_id = request.form.get('tipo_ausencia_id')
    desde_str = request.form.get('fecha_inicio')
    hasta_str = request.form.get('fecha_fin')
    motivo = request.form.get('motivo')
    
    # Campos adicionales para restricciones
    turno_id = request.form.get('turno_id')
    dias_semana_raw = request.form.getlist('dias_semana[]') 
    
    if not all([tid, tipo_id, desde_str, hasta_str]):
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios.'}), 400
        
    try:
        tipo = TipoAusencia.query.get_or_404(int(tipo_id))
        trabajador = Trabajador.query.get_or_404(int(tid))
        fecha_inicio = datetime.strptime(desde_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(hasta_str, '%Y-%m-%d').date()

        if aid and aid != '0':
            ausencia = TrabajadorAusencia.query.get_or_404(int(aid))
            # Si ya tenía una restricción técnica, la borramos para recrearla limpia
            if ausencia.restriccion:
                db.session.delete(ausencia.restriccion)
                ausencia.restriccion_id = None
            
            ausencia.trabajador_id = trabajador.id
            ausencia.tipo_ausencia_id = tipo.id
            ausencia.fecha_inicio = fecha_inicio
            ausencia.fecha_fin = fecha_fin
            ausencia.motivo = motivo
            msg = 'Registro actualizado correctamente.'
        else:
            ausencia = TrabajadorAusencia(
                trabajador_id = trabajador.id,
                tipo_ausencia_id = tipo.id,
                fecha_inicio = fecha_inicio,
                fecha_fin = fecha_fin,
                motivo = motivo
            )
            db.session.add(ausencia)
            msg = 'Registro guardado exitosamente.'
        
        db.session.flush() # Para tener ID de ausencia si es nueva

        # Sincronización con TrabajadorRestriccionTurno si es RESTRICCION
        if tipo.categoria == CategoriaAusencia.RESTRICCION:
            dias_json = [int(d) for d in dias_semana_raw] if dias_semana_raw else None
            
            # Mapeo de naturaleza según tipo (Hard por defecto)
            naturaleza = "hard"
            if tipo.tipo_restriccion == "turno_preferente":
                naturaleza = "soft"
                
            restriccion = TrabajadorRestriccionTurno(
                trabajador_id = trabajador.id,
                empresa_id    = trabajador.empresa_id,
                tipo          = tipo.tipo_restriccion,
                naturaleza    = naturaleza,
                fecha_inicio  = fecha_inicio,
                fecha_fin     = fecha_fin,
                dias_semana   = dias_json,
                turno_id      = int(turno_id) if (turno_id and turno_id != '0') else None,
                motivo        = motivo,
                activo        = True
            )
            db.session.add(restriccion)
            db.session.flush()
            ausencia.restriccion_id = restriccion.id
            
        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

@ausencia_bp.route('/ausencias/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    ausencia = TrabajadorAusencia.query.get_or_404(id)
    try:
        # Si tiene una restricción técnica vinculada, la borramos
        if ausencia.restriccion:
            db.session.delete(ausencia.restriccion)
            
        db.session.delete(ausencia)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Registro eliminado correctamente.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

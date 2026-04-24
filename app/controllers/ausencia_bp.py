from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.database import db
from app.models.business import Trabajador, TrabajadorAusencia, TipoAusencia
from app.services.capacidad_service import calcular_capacidad_detallada
from datetime import date, datetime

ausencia_bp = Blueprint('ausencia', __name__)

@ausencia_bp.route('/ausencias')
def index():
    # En un sistema multi-tenant real, empresa_id vendría de la sesión
    # Para efectos de la demo, tomamos la empresa del primer trabajador
    t_first = Trabajador.query.first()
    empresa_id = t_first.empresa_id if t_first else 1
    
    mes = int(request.args.get('mes', date.today().month))
    anio = int(request.args.get('anio', date.today().year))
    
    # Obtener todas las ausencias registradas (puedes filtrar por mes si la tabla es grande)
    ausencias = TrabajadorAusencia.query.join(Trabajador).filter(
        Trabajador.empresa_id == empresa_id
    ).order_by(TrabajadorAusencia.fecha_inicio.desc()).all()
    
    # Calcular capacidad detallada para el mes seleccionado
    capacidad = calcular_capacidad_detallada(empresa_id, mes, anio)
    
    # Datos para los selectores del modal
    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Trabajador.nombre).all()
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
def modal_nueva(id=None):
    ausencia = None
    if id:
        ausencia = TrabajadorAusencia.query.get_or_404(id)
        
    t_first = Trabajador.query.first()
    empresa_id = t_first.empresa_id if t_first else 1
    trabajadores = Trabajador.query.filter_by(empresa_id=empresa_id, activo=True).order_by(Trabajador.nombre).all()
    tipos = TipoAusencia.query.filter_by(activo=True).all()
    return render_template('modal-ausencia.html', trabajadores=trabajadores, tipos=tipos, ausencia=ausencia)

@ausencia_bp.route('/ausencias/impacto', methods=['POST'])
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
def guardar():
    aid = request.form.get('id')
    tid = request.form.get('trabajador_id')
    tipo_id = request.form.get('tipo_ausencia_id')
    desde = request.form.get('fecha_inicio')
    hasta = request.form.get('fecha_fin')
    motivo = request.form.get('motivo')
    
    if not all([tid, tipo_id, desde, hasta]):
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios.'}), 400
        
    try:
        if aid and aid != '0':
            ausencia = TrabajadorAusencia.query.get_or_404(int(aid))
            ausencia.trabajador_id = int(tid)
            ausencia.tipo_ausencia_id = int(tipo_id)
            ausencia.fecha_inicio = datetime.strptime(desde, '%Y-%m-%d').date()
            ausencia.fecha_fin = datetime.strptime(hasta, '%Y-%m-%d').date()
            ausencia.motivo = motivo
            msg = 'Ausencia actualizada correctamente.'
        else:
            ausencia = TrabajadorAusencia(
                trabajador_id = int(tid),
                tipo_ausencia_id = int(tipo_id),
                fecha_inicio = datetime.strptime(desde, '%Y-%m-%d').date(),
                fecha_fin = datetime.strptime(hasta, '%Y-%m-%d').date(),
                motivo = motivo
            )
            db.session.add(ausencia)
            msg = 'Ausencia registrada exitosamente.'
            
        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

@ausencia_bp.route('/ausencias/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    ausencia = TrabajadorAusencia.query.get_or_404(id)
    try:
        db.session.delete(ausencia)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Ausencia eliminada correctamente.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': f'Error: {str(e)}'}), 500

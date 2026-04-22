from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.business import Turno, Empresa
from datetime import datetime

turno_bp = Blueprint('turno', __name__, url_prefix='/turnos')

@turno_bp.route('/')
def index():
    registros = Turno.query.order_by(Turno.nombre).all()
    empresas_filtro = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('turnos.html', registros=registros, empresas_filtro=empresas_filtro)

@turno_bp.route('/tabla')
def tabla():
    empresa_id = request.args.get('empresa_id', '0')
    query = Turno.query
    if empresa_id != '0':
        query = query.filter_by(empresa_id=int(empresa_id))
    registros = query.order_by(Turno.nombre).all()
    return render_template('partials/turno_cards.html', registros=registros)



@turno_bp.route('/modal', methods=['POST'])
def modal():
    modo = request.form.get('modo', 'Agregar')
    registro_id = request.form.get('id', None)
    registro = None
    if registro_id and registro_id != '0':
        registro = Turno.query.get_or_404(int(registro_id))
    
    empresas = Empresa.query.filter_by(activo=True).order_by(Empresa.razon_social).all()
    return render_template('modal-turno.html', modo=modo, registro=registro, empresas=empresas)

@turno_bp.route('/guardar', methods=['POST'])
def guardar():
    tid = request.form.get('id', '').strip()
    empresa_id = request.form.get('empresa_id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    abreviacion = request.form.get('abreviacion', '').strip()
    hora_inicio_str = request.form.get('hora_inicio', '').strip()
    hora_fin_str = request.form.get('hora_fin', '').strip()
    color = request.form.get('color', '#18bc9c').strip()
    dotacion = request.form.get('dotacion_diaria', '1').strip()
    activo = request.form.get('activo') == 'true'

    if not empresa_id or not nombre or not abreviacion or not hora_inicio_str or not hora_fin_str:
        return jsonify({'ok': False, 'msg': 'Faltan campos obligatorios (*).'}), 400

    try:
        # Convertir strings a objetos Time (espera formato HH:MM)
        hi = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hf = datetime.strptime(hora_fin_str, '%H:%M').time()

        if tid and tid != '0':
            turno = Turno.query.get_or_404(int(tid))
            turno.empresa_id = int(empresa_id)
            turno.nombre = nombre
            turno.abreviacion = abreviacion
            turno.hora_inicio = hi
            turno.hora_fin = hf
            turno.color = color
            turno.dotacion_diaria = int(dotacion)
            turno.activo = activo
            msg = f'Turno "{nombre}" actualizado.'
        else:
            turno = Turno(
                empresa_id=int(empresa_id),
                nombre=nombre,
                abreviacion=abreviacion,
                hora_inicio=hi,
                hora_fin=hf,
                color=color,
                dotacion_diaria=int(dotacion),
                activo=activo
            )
            db.session.add(turno)
            msg = f'Turno "{nombre}" creado.'

        db.session.commit()
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'msg': str(e)}), 500

@turno_bp.route('/eliminar', methods=['POST'])
def eliminar():
    tid = request.form.get('id', '').strip()
    turno = Turno.query.get_or_404(int(tid))
    turno.activo = False
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Turno desactivado.'})

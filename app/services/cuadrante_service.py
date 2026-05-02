from datetime import datetime
from sqlalchemy import select
from flask_login import current_user
from app import db
from app.models.scheduling import CuadranteCabecera, CuadranteAsignacion, CuadranteAuditoria
from app.models.core import Feriado
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)

def clasificar_dia(fecha, feriados_dict: dict) -> dict:
    feriado = feriados_dict.get(fecha)
    es_dom  = (fecha.weekday() == 6)
    es_fer  = feriado is not None and feriado.activo
    es_irr  = feriado.es_irrenunciable if feriado else False
    es_reg  = feriado.es_regional if feriado else False

    if es_irr and es_dom:   tipo_dia = 'domingo-irrenunciable'
    elif es_irr:            tipo_dia = 'feriado-irrenunciable'
    elif es_fer and es_dom: tipo_dia = 'domingo-feriado'
    elif es_reg:            tipo_dia = 'feriado-regional'
    elif es_fer:            tipo_dia = 'feriado'
    elif es_dom:            tipo_dia = 'domingo'
    else:                   tipo_dia = 'normal'

    return {
        'es_feriado': es_fer, 'es_domingo': es_dom,
        'es_irrenunciable': es_irr, 'es_feriado_regional': es_reg,
        'tipo_dia': tipo_dia
    }


def guardar_cuadrante(empresa_id, servicio_id,
                      mes, anio, asignaciones: list, ip: str = None) -> CuadranteCabecera:
    """
    Persiste el cuadrante generado por el Solver.
    """
    try:
        from datetime import date
        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, monthrange(anio, mes)[1])
        feriados = db.session.execute(
            select(Feriado).where(
                Feriado.fecha.between(primer_dia, ultimo_dia),
                Feriado.activo == True
            )
        ).scalars().all()
        feriados_dict = {f.fecha: f for f in feriados}

        # Si ya existe un cuadrante para este período, eliminarlo (reemplazar)
        existente = db.session.execute(
            select(CuadranteCabecera).where(
                CuadranteCabecera.empresa_id == empresa_id,
                CuadranteCabecera.servicio_id == servicio_id,
                CuadranteCabecera.mes == mes,
                CuadranteCabecera.anio == anio
            )
        ).scalar_one_or_none()

        if existente:
            db.session.delete(existente)
            db.session.flush()

        # Crear cabecera
        cabecera = CuadranteCabecera(
            empresa_id=empresa_id,
            servicio_id=servicio_id,
            mes=mes, anio=anio,
            estado='guardado',
            generado_por_user_id=current_user.id,
            guardado_por_user_id=current_user.id,
            guardado_en=datetime.utcnow()
        )
        db.session.add(cabecera)
        db.session.flush()

        # Insertar asignaciones
        from datetime import datetime as dt
        for a in asignaciones:
            fecha_str = a['fecha']
            fecha_obj = dt.strptime(fecha_str, '%Y-%m-%d').date()
            
            flags = clasificar_dia(fecha_obj, feriados_dict)
            origen = a.get('origen', 'solver')
            
            asignacion = CuadranteAsignacion(
                cabecera_id=cabecera.id,
                trabajador_id=a['trabajador_id'],
                fecha=fecha_obj,
                turno_id=a.get('turno_id'),
                es_libre=a.get('es_libre', False),
                horas_asignadas=a.get('horas_asignadas', 0),
                origen=origen,
                **flags
            )
            db.session.add(asignacion)
            
            if origen == 'manual':
                db.session.flush()
                db.session.add(CuadranteAuditoria(
                    asignacion_id=asignacion.id,
                    cabecera_id=cabecera.id,
                    user_id=current_user.id,
                    turno_anterior_id=None,
                    turno_nuevo_id=a.get('turno_id'),
                    era_libre_antes=None,
                    es_libre_ahora=a.get('es_libre', False),
                    ip_address=ip,
                    motivo='Ajuste manual antes de guardar'
                ))

        db.session.commit()
        return cabecera
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error al guardar cuadrante: {str(e)}")
        raise e


def editar_asignacion_manual(cabecera_id: int, trabajador_id: int, fecha: str,
                              turno_nuevo_id, es_libre: bool, motivo: str, ip: str) -> CuadranteAsignacion:
    """
    Modifica una asignación post-guardado con rollback seguro.
    """
    try:
        from datetime import datetime as dt
        fecha_obj = dt.strptime(fecha, '%Y-%m-%d').date()
        
        asig = db.session.execute(
            select(CuadranteAsignacion).where(
                CuadranteAsignacion.cabecera_id == cabecera_id,
                CuadranteAsignacion.trabajador_id == trabajador_id,
                CuadranteAsignacion.fecha == fecha_obj
            )
        ).scalar_one_or_none()

        if not asig:
            raise ValueError(f"Asignación no encontrada")

        # Registrar auditoría ANTES de modificar
        db.session.add(CuadranteAuditoria(
            asignacion_id=asig.id,
            cabecera_id=asig.cabecera_id,
            user_id=current_user.id,
            turno_anterior_id=asig.turno_id,
            turno_nuevo_id=turno_nuevo_id,
            era_libre_antes=asig.es_libre,
            es_libre_ahora=es_libre,
            ip_address=ip,
            motivo=motivo
        ))

        # Actualizar asignación
        asig.turno_id               = turno_nuevo_id
        asig.es_libre               = es_libre
        asig.origen                 = 'manual'
        asig.modificado_por_user_id = current_user.id
        asig.modificado_en          = dt.utcnow()

        db.session.commit()
        return asig
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error en edición manual de asignación: {str(e)}")
        raise e

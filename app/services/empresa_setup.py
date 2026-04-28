"""
Auto-setup al crear una empresa.
Refactorizado: Se llama explícitamente desde el controlador para evitar advertencias de sesión.
"""

def ejecutar_setup_empresa(empresa):
    """
    Crea la configuración base para una nueva empresa.
    Debe llamarse después de db.session.flush() o db.session.commit()
    pero dentro de la misma transacción o en una nueva.
    """
    from app.database import db
    from app.models.business import (
        Turno, TipoAusencia, ReglaEmpresa,
        TurnoPlantilla, TipoAusenciaPlantilla, Regla, Servicio
    )

    # 1. Turnos base desde plantillas
    for p in TurnoPlantilla.query.filter_by(activo=True).all():
        db.session.add(Turno(
            empresa_id=empresa.id, nombre=p.nombre,
            abreviacion=p.abreviacion, hora_inicio=p.hora_inicio,
            hora_fin=p.hora_fin, color=p.color,
            dotacion_diaria=p.dotacion_diaria, es_nocturno=p.es_nocturno,
            es_base=True, activo=True,
        ))

    # 2. Tipos de ausencia base desde plantillas
    for p in TipoAusenciaPlantilla.query.filter_by(activo=True).all():
        db.session.add(TipoAusencia(
            empresa_id=empresa.id, nombre=p.nombre,
            abreviacion=p.abreviacion, color=p.color,
            es_base=True, activo=True,
        ))

    # 3. Reglas legales asignadas
    for r in Regla.query.filter_by(activo=True).all():
        db.session.add(ReglaEmpresa(
            empresa_id=empresa.id, regla_id=r.id,
            params_custom=None, es_base=True, activo=True,
        ))

    # 4. Vincular todos los servicios activos
    for s in Servicio.query.filter_by(activo=True).all():
        empresa.servicios.append(s)
    
    db.session.flush()

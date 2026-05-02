# app/scheduler/feriado_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="America/Santiago")


def iniciar_scheduler_feriados(app):
    """
    Registra el job de sincronización mensual de feriados.
    Llamar desde app/__init__.py al arrancar la aplicación.

    El job corre el día 1 de cada mes a las 02:00 AM (hora Chile).
    Consulta los feriados del mes siguiente y actualiza la BD.
    """
    from app.services.feriado_sync_service import sincronizar_mes_siguiente

    def job_sync():
        with app.app_context():
            logger.info("[FeriadoScheduler] Iniciando sincronización mensual...")
            resultado = sincronizar_mes_siguiente()
            logger.info(f"[FeriadoScheduler] Completado: {resultado}")

    # Día 1 de cada mes a las 02:00 AM hora Chile
    scheduler.add_job(
        func=job_sync,
        trigger=CronTrigger(day=1, hour=2, minute=0, timezone="America/Santiago"),
        id="sync_feriados_mensual",
        name="Sincronización mensual de feriados",
        replace_existing=True,
        misfire_grace_time=3600  # Tolera hasta 1 hora de retraso si el servidor estaba caído
    )

    scheduler.start()
    logger.info("[FeriadoScheduler] Scheduler iniciado. Job programado para el día 1 de cada mes a las 02:00.")
    return scheduler


def detener_scheduler_feriados():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[FeriadoScheduler] Scheduler detenido.")

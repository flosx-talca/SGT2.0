# app/services/feriado_sync_service.py

import requests
import logging
from datetime import date, datetime
from app.models.core import Feriado
from app import db
import os
import requests

logger = logging.getLogger(__name__)

FERIADOS_API_KEY  = os.environ.get("FERIADOS_API_KEY", "frd_79c25cdc001441e59cc3dd4dae2e125b")
FERIADOS_BASE_URL = "https://api.feriados.io/v1/CL"
FERIADOS_HEADERS  = {"Authorization": f"Bearer {FERIADOS_API_KEY}"}

# Feriados irrenunciables conocidos (Ley 19.973) — fallback si la API no los marca
IRRENUNCIABLES_CONOCIDOS = {
    (1, 1),   # 1 enero
    (5, 1),   # 1 mayo
    (9, 18),  # 18 septiembre
    (9, 19),  # 19 septiembre
    (12, 25), # 25 diciembre
}


def es_irrenunciable(mes: int, dia: int, nombre: str = "") -> bool:
    """
    Determina si un feriado es irrenunciable por fecha o nombre.
    La API feriados.io retorna el campo irrenunciable=True/False.
    Este fallback cubre si la API no lo indica explícitamente.
    """
    return (mes, dia) in IRRENUNCIABLES_CONOCIDOS


def sincronizar_feriados_anio(anio: int) -> dict:
    """
    Consulta la API feriados.io para el año indicado y sincroniza con la BD.
    Solo inserta o actualiza registros con diferencias reales.
    Retorna un resumen de la operación.
    """
    url = f"{FERIADOS_BASE_URL}/holidays/{anio}"
    resumen = {"anio": anio, "consultados": 0, "insertados": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}

    try:
        resp = requests.get(url, headers=FERIADOS_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise ValueError(f"API retornó error: {data}")

        feriados_api = data.get("data", [])
        resumen["consultados"] = len(feriados_api)

        for item in feriados_api:
            try:
                fecha      = date.fromisoformat(item["date"])
                descripcion = item.get("name", "Feriado")
                tipo_api   = item.get("type", "national")   # national | regional
                irr_api    = item.get("irrenunciable", False)

                # Determinar clasificación
                es_irr = irr_api or es_irrenunciable(fecha.month, fecha.day, descripcion)
                es_reg = (tipo_api == "regional")
                tipo   = "irrenunciable" if es_irr else ("regional" if es_reg else "nacional")
                regiones_api = item.get("regions")
                regiones_str = ",".join(regiones_api) if isinstance(regiones_api, list) else None

                # Buscar si ya existe en BD
                existente = Feriado.query.filter_by(fecha=fecha).first()

                if existente is None:
                    # Insertar nuevo
                    nuevo = Feriado(
                        fecha=fecha,
                        descripcion=descripcion,
                        es_irrenunciable=es_irr,
                        es_regional=es_reg,
                        tipo=tipo,
                        regiones=regiones_str,
                        activo=True,
                        fuente="feriados.io"
                    )
                    db.session.add(nuevo)
                    resumen["insertados"] += 1

                else:
                    # Verificar si hay diferencias antes de actualizar
                    cambios = False
                    if existente.descripcion != descripcion:
                        existente.descripcion = descripcion
                        cambios = True
                    if existente.es_irrenunciable != es_irr:
                        existente.es_irrenunciable = es_irr
                        cambios = True
                    if existente.es_regional != es_reg:
                        existente.es_regional = es_reg
                        cambios = True
                    if existente.tipo != tipo:
                        existente.tipo = tipo
                        cambios = True
                    if existente.regiones != regiones_str:
                        existente.regiones = regiones_str
                        cambios = True

                    if cambios:
                        existente.actualizado_en = datetime.utcnow()
                        resumen["actualizados"] += 1
                    else:
                        resumen["sin_cambios"] += 1

            except Exception as e:
                resumen["errores"].append(f"{item.get('date', '?')} — {str(e)}")

        db.session.commit()
        logger.info(f"[FeriadoSync] Año {anio}: {resumen}")

    except requests.RequestException as e:
        resumen["errores"].append(f"Error de red: {str(e)}")
        logger.error(f"[FeriadoSync] Error consultando API para {anio}: {e}")

    return resumen


def sincronizar_mes_siguiente() -> dict:
    """
    Sincroniza los feriados del mes siguiente al actual.
    Diseñado para ser llamado por el scheduler mensual.
    Usa el endpoint por mes para minimizar uso de quota de la API.
    """
    hoy = date.today()
    if hoy.month == 12:
        mes_sig, anio_sig = 1, hoy.year + 1
    else:
        mes_sig, anio_sig = hoy.month + 1, hoy.year

    url = f"{FERIADOS_BASE_URL}/holidays/{anio_sig}/{mes_sig}"
    resumen = {"mes": f"{anio_sig}-{mes_sig:02d}", "insertados": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}

    try:
        resp = requests.get(url, headers=FERIADOS_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise ValueError(f"API error: {data}")

        for item in data.get("data", []):
            try:
                fecha       = date.fromisoformat(item["date"])
                descripcion = item.get("name", "Feriado")
                tipo_api    = item.get("type", "national")
                irr_api     = item.get("irrenunciable", False)
                es_irr      = irr_api or es_irrenunciable(fecha.month, fecha.day)
                es_reg      = (tipo_api == "regional")
                tipo        = "irrenunciable" if es_irr else ("regional" if es_reg else "nacional")
                regiones_api = item.get("regions")
                regiones_str = ",".join(regiones_api) if isinstance(regiones_api, list) else None

                existente = Feriado.query.filter_by(fecha=fecha).first()
                if existente is None:
                    db.session.add(Feriado(
                        fecha=fecha, descripcion=descripcion,
                        es_irrenunciable=es_irr, es_regional=es_reg,
                        tipo=tipo, regiones=regiones_str, activo=True, fuente="feriados.io"
                    ))
                    resumen["insertados"] += 1
                else:
                    # Solo actualizar si hay diferencias
                    cambios = any([
                        existente.descripcion != descripcion,
                        existente.es_irrenunciable != es_irr,
                        existente.tipo != tipo,
                        existente.regiones != regiones_str,
                    ])
                    if cambios:
                        existente.descripcion    = descripcion
                        existente.es_irrenunciable = es_irr
                        existente.tipo           = tipo
                        existente.regiones       = regiones_str
                        existente.actualizado_en = datetime.utcnow()
                        resumen["actualizados"] += 1
                    else:
                        resumen["sin_cambios"] += 1

            except Exception as e:
                resumen["errores"].append(str(e))

        db.session.commit()
        logger.info(f"[FeriadoSync] Mes siguiente: {resumen}")

    except requests.RequestException as e:
        resumen["errores"].append(str(e))

    return resumen


def carga_inicial(anios: list = None) -> dict:
    """
    Pobla la tabla feriado desde cero.
    Llamar una sola vez al desplegar el sistema por primera vez.
    Por defecto sincroniza el año actual y el siguiente.
    """
    if anios is None:
        hoy = date.today()
        anios = [hoy.year]

    resultados = {}
    for anio in anios:
        resultados[anio] = sincronizar_feriados_anio(anio)
    return resultados


def verificar_dia_habil(fecha: str, region: str = None) -> dict:
    """
    Llama a la API de feriados.io para verificar si una fecha es día hábil.
    Soporta verificación subnacional enviando el parámetro region.
    """
    url = f"{FERIADOS_BASE_URL}/is-business-day"
    params = {"date": fecha}
    if region:
        params["region"] = region

    try:
        resp = requests.get(url, headers=FERIADOS_HEADERS, params=params, timeout=5)
        resp.raise_for_status()
        data_json = resp.json()
        if data_json.get("success"):
            payload = data_json.get("data", {})
            return {
                "ok": True, 
                "is_business_day": payload.get("is_business_day"),
                "date": payload.get("date"),
                "region": payload.get("region"),
                "day_of_week": payload.get("day_of_week")
            }
        else:
            return {"ok": False, "msg": f"API Error: {data_json}"}
    except Exception as e:
        logger.error(f"[FeriadoSync] Error en is-business-day para {fecha}: {e}")
        return {"ok": False, "msg": str(e)}

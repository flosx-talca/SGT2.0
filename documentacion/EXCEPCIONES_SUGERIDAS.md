# Informe: Mejoras Sugeridas en Manejo de Excepciones - SGT 2.1

Este documento detalla los puntos críticos identificados en la arquitectura actual del sistema donde la falta de control de excepciones podría comprometer la estabilidad del servidor o la integridad de los datos.

## 1. Gestión de Errores Global (Capa de Aplicación)
**Hallazgo:** No existen manejadores de errores globales (`@app.errorhandler`) en `app/__init__.py`.
**Riesgo:** Cualquier error no capturado devuelve una página HTML 500 estándar. Esto rompe la integración con **HTMX** (el modal desaparece o se queda en blanco) y puede exponer trazas de error sensibles si no se configura correctamente.
**Sugerencia:**
- Implementar manejadores para errores `404`, `500` y `Exception` general.
- Retornar fragmentos HTML específicos si la petición es HTMX (usando el header `HX-Request`) o JSON si es una API.

## 2. Transacciones de Base de Datos (Integridad)
**Hallazgo:** Múltiples rutas (ej: `turno_bp.eliminar`, `cuadrante_service.py`) ejecutan `db.session.commit()` sin un bloque `try-except` que incluya `db.session.rollback()`.
**Riesgo:** Si un commit falla (ej: violación de llave foránea o pérdida de conexión), la sesión queda "sucia". Las peticiones siguientes del mismo hilo del servidor podrían fallar en cascada debido a una transacción pendiente fallida.
**Sugerencia:**
- Envolver todos los `commit()` en bloques `try/except`.
- Asegurar `db.session.rollback()` en el bloque `except`.

## 3. Robustez en el Motor de Planificación (Solver)
**Hallazgo:** Existen cálculos en `planificacion_bp.py` que dependen de la existencia de datos maestros.
**Riesgo:** 
- **División por cero:** Si un usuario crea un turno con duración `0` o no hay turnos cargados, el cálculo de metas mensuales lanzará un `ZeroDivisionError` en el servidor.
- **Datos Nulos:** El acceso a `t.tipo_contrato.name` fallará si un trabajador no tiene contrato asignado.
**Sugerencia:**
- Validar `len(turnos) > 0` antes de promediar duraciones.
- Usar `.get()` o validaciones previas para atributos obligatorios en el Solver.

## 4. Comunicación de Errores a la UI (HTMX/ToastR)
**Hallazgo:** Los errores en las peticiones AJAX a veces retornan texto plano.
**Riesgo:** El usuario no recibe feedback visual de por qué falló una acción (ej: "No se pudo guardar").
**Sugerencia:**
- Estandarizar la respuesta de error para que incluya un header `HX-Trigger: {"mostrarToast": {"msg": "Error...", "type": "error"}}`.
- Crear una plantilla de error parcial para mostrar dentro de los modales.

## 5. Auditoría y Logging
**Hallazgo:** La aplicación utiliza mayoritariamente `print()` para depuración en lugar del módulo `logging`.
**Riesgo:** En producción, los `print()` son difíciles de rastrear, no tienen marca de tiempo y pueden saturar los logs del servidor sin estructura.
**Sugerencia:**
- Configurar un logger rotativo en `app/__init__.py`.
- Registrar excepciones críticas con `logger.exception(e)` para capturar el stack trace completo en el archivo de logs.

---
**Próximos Pasos Recomendados:**
1. Crear un archivo `app/utils/errors.py` con decoradores de manejo de excepciones.
2. Refactorizar `cuadrante_service.py` para incluir transacciones atómicas seguras.
3. Implementar el manejador global en `create_app()`.

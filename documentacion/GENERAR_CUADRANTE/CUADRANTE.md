# Itinerario y Estado de Desarrollo: Módulo de Cuadrantes SGT 2.1

Este documento detalla el progreso actual en el rediseño y acoplamiento del motor de planificación (OR-Tools) hacia el nuevo ecosistema de almacenamiento, auditoría y manipulación de datos de SGT 2.1.

---

## 🟢 Lo Realizado (Completado)

### 1. Migración Arquitectónica de Modelos (Backend)
- **Desvinculación de `sucursal_id`**: Adaptación de los modelos `CuadranteCabecera`, `CuadranteAsignacion` y `CuadranteAuditoria` para utilizar la jerarquía principal de la aplicación (`empresa_id`).
- **Múltiples Servicios**: Ajuste de constraints (`uq_cuadrante_periodo`) en base de datos para permitir múltiples planificaciones por Empresa dentro de un mismo mes, diferenciadas por el `servicio_id`.
- **Inyección de Dependencias de Contexto**: Corrección del flujo de renderizado en `planificacion_bp.py` y `main_bp.py` para asegurar que `empresa_activa` es capturado de manera segura y proporcionado a toda la vista.

### 2. Persistencia y Almacenamiento
- **Servicio Idempotente (`cuadrante_service.py`)**: Implementación del método `guardar_cuadrante()`. Capaz de recibir el resultado de OR-Tools en JSON y registrarlo en base de datos.
- **Clasificación Legal Nativa**: Durante la persistencia, el sistema inyecta en la base de datos las etiquetas de los días (`es_feriado`, `es_domingo`, `es_irrenunciable`) comparándolos con el repositorio de feriados activo de la memoria.

### 3. Edición Manual y Auditoría (Modo Edición)
- **Recarga de Estado (`GET /planificacion/editar/<id>`)**: Creación del endpoint para la reconstitución del Cuadrante. Lee los datos previamente persistidos y renderiza el generador simulado (`simulacion.html`) bajo un contexto de modo "Edición" (sin opciones de re-generar).
- **Asignación en Caliente (`PUT /cuadrante/asignacion`)**: Endpoint API adaptado para modificar celdas individuales basado en claves naturales (Fecha + ID Trabajador) sin depender de IDs subyacentes escondidos.
- **Micro-interacciones UI JS**: Se implementó el `turno_picker` con botones de colores. Al clickear sobre una celda ya guardada en modo edición, se envía un PUT por AJAX, validando y guardando un registro de Auditoría.
- **Auditoría Integral**: Los cambios manuales realizados antes del primer guardado (en simulación) ahora también generan registros de auditoría y persisten la marca "U" correctamente.
- **Visualización Estricta (Modo Lectura)**: Implementado el endpoint `GET /planificacion/ver/<id>`. En este modo, la interacción está bloqueada mediante una capa de interfaz que deshabilita eventos JS, se ocultan botones de generación/edición y se notifica al usuario que es solo lectura.
- **Dashboard en Tiempo Real**: Reemplazado el "mockup" estático del Dashboard con HTMX, que carga de manera asíncrona la lista de "Últimas Planificaciones" de la BD.

---

## 🟡 Lo Pendiente (Próximos Pasos)

### 1. Exportación de Datos (PDF / Excel)
- **Reportes Legales**: El usuario necesitará exportar su planificación en un formato válido ante la Dirección del Trabajo (DT).
### 1. Generación de Reportes (COMPLETADO ✅)
- **Estado**: Finalizado. Implementados motores de exportación para Excel (openpyxl) y PDF (ReportLab).
- **Características**:
    - **Excel**: Diseño vertical con marcado de feriados, colores de turnos y totales mensuales por trabajador.
    - **PDF Premium**: Medidas exactas (15.4cm de ancho), nombres horizontales, bordes de sección gruesos y nombres de archivos dinámicos (`Empresa_Servicio_Periodo`).
    - **Ajuste**: Todo el mes (31 días) garantizado en una sola página tamaño Carta.

### 2. Estados de Flujo del Cuadrante (IMPLEMENTADO ✅)
- **Funcionalidad**: Los botones de acción en la UI ahora responden al estado del cuadrante.
- **Bloqueo**: Al estar en estado `"publicado"`, el sistema bloquea el picker de turnos y muestra un aviso de "Modo Lectura".
- **Publicación**: Botón de "Publicar Cuadrante" funcional que vuelve inmutable la planificación.

### 4. Recálculo Reactivo Local de Métricas (COMPLETADO ✅)
- **Logro**: Implementada la función `SGT.actualizarContadoresFila()` en JS.
- **Efecto**: Al realizar una edición manual post-guardado, el sistema recalcula en tiempo real las horas del trabajador, la dotación diaria (defecto/superávit) y las métricas globales del dashboard sin recargar la página.

### 5. Validaciones de Edición Manual (PENDIENTE ⏳)
- **Objetivo**: Integrar las reglas de la DT (Dirección del Trabajo) en el picker manual.
- **Acción futura**: Si un usuario cambia manualmente un turno 'Libre' a un turno de 'Noche', el sistema deberá evaluar si este acto viola una regla dura y arrojar una advertencia (ToastR).

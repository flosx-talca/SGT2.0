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
- **Micro-interacciones UI JS**: Se implementó una lógica de reemplazo donde, al clickear sobre una celda ya guardada, se invoca un `select` autogenerado con los turnos vigentes, enviando un PUT por AJAX, validando y guardando un registro de Auditoría.
- **Dashboard en Tiempo Real**: Reemplazado el "mockup" estático del Dashboard con HTMX, que carga de manera asíncrona la lista de "Últimas Planificaciones" de la BD.

---

## 🟡 Lo Pendiente (Próximos Pasos)

### 1. Visualización Estricta (Modo Lectura)
- **Implementar `GET /planificacion/ver/<id>`**: Aunque actualmente tenemos el modo editar, el dashboard posee un botón de visualización con el ícono del ojo (👁️). Debemos instanciar la misma plantilla `simulacion.html` con `modo='ver'` para bloquear completamente cualquier interacción en el JS, impidiendo cambios y quitando los cursores en forma de puntero.

### 2. Exportación de Datos (PDF / Excel)
- **Reportes Legales**: El usuario necesitará exportar su planificación en un formato válido ante la Dirección del Trabajo (DT).
- **Implementación sugerida**: Desarrollar un endpoint `/cuadrante/exportar/<id>` que reconstruya el cuadrante usando Pandas o ReportLab (u otra librería) para generar un documento listo para la firma de los trabajadores.

### 3. Estados de Flujo del Cuadrante (Publicación)
- El estado actual en base de datos es `"guardado"`. El sistema debe definir el comportamiento frente a un "Cuadrante Publicado" (cuando el estado cambia de `guardado` a `publicado`).
- **Bloqueo**: Una vez publicado, la lógica de negocio posiblemente deba prevenir modificaciones arbitrarias o, si se permite, requerir autorizaciones adicionales de Super-Admin.

### 4. Recálculo Reactivo Local de Métricas
- Actualmente, al realizar una **edición manual** post-guardado, las insignias de déficit/superávit en la columna derecha de la tabla (`<td class="cob-val">`) y los totales (eje inferior de horas) no se actualizan en el acto en el HTML.
- **Acción requerida**: Desarrollar la re-evaluación algorítmica vía JS post-AJAX para que los números inferiores y laterales cuadren inmediatamente.

### 5. Validaciones de Edición Manual
- Si un usuario cambia manualmente un turno 'Libre' a un turno de 'Noche', el sistema debería evaluar si este acto **viola una regla dura** (como falta de descanso post-noche) y arrojar un ToastR de advertencia o impedir la acción según decida el equipo funcional.

# CHECKLIST DE MEJORAS - MOTOR DE PLANIFICACIÓN SGT 2.1

Este documento sirve como hoja de ruta para la estabilización del Builder. Cada ítem debe probarse de forma independiente.

## FASE 1: Estabilización de Pesos (Prioridad Alta)
*Objetivo: Lograr que el sistema respete la dotación mínima y no asigne gente de más.*

- [ ] **1.1 Ajuste de Pesos en `builder.py`**: Subir `W_EXCESO` a 100,000 y bajar `W_META` a 50,000.
- [ ] **1.2 Desbalance de Premio**: Asegurar que `W_EXCESO` sea mayor que `W_REWARD` para que sobrar gente tenga un costo neto real.
- [ ] **1.3 Validación**: Probar con 3 trabajadores y dotación 1. El sistema debería dar ~10 días a cada uno.

## FASE 2: Metas Dinámicas y Contractuales
*Objetivo: Que el objetivo de días de cada trabajador se base en su contrato real.*

- [ ] **2.1 Cálculo de Meta Individual**: Modificar `builder.py` para calcular la meta usando `(horas_semanales / duracion_turno)` de cada trabajador.
- [ ] **2.2 Eliminación de Valores en Duro**: Quitar el `42.0` por defecto y forzar la lectura desde el objeto trabajador.
- [ ] **2.3 Validación**: Probar con un trabajador de 20h y uno de 42h. Sus metas de días deben ser distintas en el log del solver.

## FASE 3: Parametrización Total (Base de Datos)
*Objetivo: Controlar el motor sin tocar el código.*

- [ ] **3.1 Migración de Pesos**: Mover las constantes `W_...` de `builder.py` a la tabla `parametro_legal`.
- [ ] **3.2 Carga vía ConfigManager**: Modificar el Builder para que use `ConfigManager.get_int()` para todos los pesos.
- [ ] **3.3 Validación**: Cambiar un peso en la BD y verificar que el comportamiento del solver cambia sin reiniciar el servidor.

## FASE 4: Precisión Legal y Nocturnidad
*Objetivo: Eliminar estimaciones y usar datos reales.*

- [ ] **4.1 Inyección de Turno en Motor Legal**: Pasar el objeto `MockTurno` en todas las llamadas a `resumen_legal` dentro del Builder.
- [ ] **4.2 Checkbox Nocturno en UI**: Añadir campo manual en el formulario de Turnos para marcar nocturnidad sin depender del cálculo de horas.
- [ ] **4.3 Validación**: Crear un turno que termina a las 23:59 y marcarlo como nocturno manualmente. Verificar que aplica el descanso de 12h.

## FASE 5: Robustez y UX
*Objetivo: Calidad de producto final.*

- [ ] **5.1 Mejora de Mensajes de Conflicto**: Que el sistema diga qué regla falló (ej: "Exceso de horas en Worker X").
- [ ] **5.2 Validaciones de Formulario**: Impedir guardar turnos con duraciones negativas o inconsistentes.
- [ ] **5.3 Regla de Bienestar**: Añadir "Soft Rule" para preferir días libres consecutivos (fines de semana).

---
**Instrucciones de uso**: Marcar con `[x]` cada tarea completada tras verificar su funcionamiento.

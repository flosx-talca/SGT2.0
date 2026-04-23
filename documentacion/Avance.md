# Avances del Proyecto: SGT 2.0 - Motor de IA

## Estado Actual: **Estable y Optimizado**
En esta sesión se han resuelto los bloqueos críticos que impedían que la IA generara cuadrantes válidos y equilibrados.

### ✅ Logros Técnicos
1.  **Cumplimiento Legal Estricto:**
    *   Implementación de la **Ley 6x2** (2 días libres tras 6 trabajados) como restricción matemática dura.
    *   Garantía de **2 Domingos Libres** al mes por trabajador (Hard Rule).
2.  **Flexibilidad Operativa:**
    *   **Dotación Variable:** Capacidad de definir requerimientos distintos para los domingos, permitiendo resolver cuellos de botella de personal.
    *   **Lógica de Contratos:** El sistema ahora distingue entre trabajadores de 45h, 30h y 20h, ajustando sus topes de carga automáticamente.
3.  **Equidad de Carga (Fairness):**
    *   Se añadió un algoritmo de balanceo que minimiza la diferencia de turnos entre trabajadores, evitando que unos trabajen mucho y otros nada.
4.  **Estabilidad del Solver:**
    *   Conversión de Preferencias a **Reglas Suaves**. El sistema ya no falla con "Error 400" si hay conflictos; en su lugar, prioriza la Ley y la Cobertura.
    *   Aumento del tiempo de optimización a **30 segundos**.

### 🐛 Errores Corregidos
-   **DB Fix:** Se reparó la tabla de ausencias para aceptar el campo `motivo` que faltaba, permitiendo guardar fichas de trabajadores.
-   **Crash Fix:** Se corrigió el error de importación de `sys` en el controlador que causaba caídas del servidor al generar cuadrantes.

### 🚀 Próximos Pasos (Rama OPTIMIZACION)
-   Implementar **Ruptura de Simetrías** para acelerar el cálculo en sucursales con muchos trabajadores idénticos.
-   Habilitar **Paralelismo** en el solver para usar todos los núcleos del servidor.
-   Añadir **Validación Previa** de dotación para alertar al usuario sobre faltas de personal antes de iniciar la IA.

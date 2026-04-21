# SGT 2.1 - Prototipo Frontend Estático (TEMPLATES_UNI)

Este directorio contiene una versión **100% estática y funcional** del frontend de SGT (Sistema de Gestión de Turnos), compilada para trabajar independientemente del backend en Python. Es ideal para pruebas de concepto, diseño UI/UX y flujos de usuario sin necesidad de servidor.

---

## 🗂️ Directorio de Páginas y su Función

Cada archivo `.html` representa una vista principal del sistema. Puedes navegar entre ellas usando el menú lateral.

### 1. Gestión de Maestros
- **`clientes.html` [NUEVO]**: Mantenedor de clientes (dueños/administradores de empresas). Permite gestión multi-empresa.
- **`trabajadores.html`**: Directorio central de personal. Permite visualizar el estado (Activo/Inactivo), cargo, tipo de contrato (Full/Part-time) y horas semanales.
- **`empresas.html`**: Listado de empresas con vinculación jerárquica a clientes mediante búsqueda avanzada Select2.
- **`servicios.html`**: Configuración de unidades de negocio (Pronto, Gasolinera, Lavado).
- **`turnos.html`**: Definición técnica de turnos con horarios y colores.

### 2. Operaciones y Motor de Reglas (Arquitectura Tripartita)
- **`simulacion.html`** (Planificación): La joya de la corona. Matriz interactiva para asignación de turnos con validación de dotación en tiempo real.
- **`reglas-familias.html`**: Gestión de **Lógica Core (Super Admin)**. Define familias de evaluación genéricas (Comparación, Rangos, Secuencias).
- **`reglas-config.html`**: Gestión de **Instancias Globales (Super Admin)**. Permite crear reglas específicas vinculándolas a familias, con un constructor de parámetros JSON dinámico.
- **`reglas-empresa.html`** [NUEVO]: Gestión de **Vista Cliente (Admin Local)**. Permite a cada empresa activar/desactivar reglas y personalizar valores sin tocar la lógica estructural.

### 3. Navegación y Dashboards
- **`index.html`**: Dashboard principal con tarjetas de acceso rápido organizadas por rol (Administración Local vs Super Admin).
- **Sidebar Unificado**: Navegación consistente en todos los módulos con una estructura jerárquica clara para facilitar el flujo de trabajo.

### 4. Acceso
- **`login.html`**: Interfaz de entrada con diseño premium.

---

## 🧩 Modales e Interactividad (Sistema Inyectado)

Para que todo funcione sin servidor, el prototipo inyecta los modales al final de cada página o los carga mediante plantillas en el archivo principal. Se ha integrado **Select2** para búsquedas y multiselección dinámica:

- **`modal-cliente.html` [NUEVO]**: Formulario con validación de RUT, email y multiselección de empresas asociadas.
- **`modal-trabajador.html`**: Versión actualizada con lógica de contrato dinámica (Horas semanales automáticas para Full-time, manuales para Part-time).
- **`modal-empresa.html`**: Incluye ahora selector de cliente asociado con motor de búsqueda Select2.
- **`modal-turno.html`**: Configuración de horarios y visualización.
- **`modal-regla-familia.html`**: Editor de lógica genérica para familias de reglas.
- **`modal-regla-config.html`**: Editor avanzado para Super Admin con generación automática de JSON.
- **`modal-regla-empresa.html`**: Interfaz simplificada para clientes que bloquea campos técnicos.

---

## 🛠️ Detalles Técnicos para Desarrolladores

### Sincronización Automática
El archivo `static/css/cuadrante.css` controla el comportamiento de la matriz de planificación. Hemos implementado:
- `width: max-content` y `min-width: 1200px` para asegurar que el scrollbar siempre esté disponible.
- Estilos personalizados para barras de desplazamiento (`-webkit-scrollbar`) que las hacen visibles y fáciles de usar.

### Independencia Local
Todas las librerías están en `static/vendor/`. El sistema **no requiere internet** para mostrar iconos, fuentes o estilos, lo que garantiza que el diseño se vea idéntico en cualquier entorno.

---

**Nota para Cursor / IA:**
Cualquier mejora orientada a estilos visuales o comportamientos del DOM debe ser practicada primero en este directorio. Los IDs de los elementos son consistentes con la lógica de producción para facilitar una migración futura.

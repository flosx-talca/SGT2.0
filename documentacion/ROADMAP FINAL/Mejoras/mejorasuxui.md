# Mejoras Futuras de UI/UX — SGT 2.1

Documento de referencia para mejoras pendientes de interfaz y experiencia de usuario.
Ordenadas por prioridad de impacto operacional.

---

## 🔴 Alta Prioridad
> Afectan la operación diaria del sistema

### 1. Menú activo al navegar con HTMX
- **Problema:** El ítem del sidebar no queda resaltado correctamente al cambiar de sección vía HTMX, porque `request.endpoint` solo se evalúa en el render inicial.
- **Solución:** Comparar la URL actual con el `href` del link en el evento `htmx:afterOnLoad` (código base ya existe, requiere ajuste fino).
- **Archivos:** `layout.html`

### 2. Deshabilitar botón Guardar durante POST
- **Problema:** El usuario puede hacer doble click en "Guardar" y enviar el formulario dos veces, creando registros duplicados.
- **Solución:** Al iniciar `$.post()`, hacer `$('button[onclick]').prop('disabled', true)` y restaurar en `.always()`.
- **Archivos:** `modal-{entidad}.html` (todos los modales)

### 3. Mensajes de error descriptivos por campo
- **Problema:** El `toastr.error()` muestra mensajes genéricos. El backend puede retornar errores por campo específico pero no se aprovecha.
- **Solución:** El backend retorna `{'ok': false, 'field': 'codigo', 'msg': '...'}` y el frontend hace focus en el campo con error + borde rojo.
- **Archivos:** `region_bp.py` (y futuros blueprints), `modal-{entidad}.html`

---

## 🟡 Media Prioridad
> Mejoran la calidad percibida del sistema

### 4. Skeleton loader en refresh de tabla
- **Problema:** Al hacer `refreshTablaEntidad()` con HTMX, el tbody queda vacío un instante antes de que lleguen los nuevos datos.
- **Solución:** Insertar filas shimmer (animación CSS gris) en `htmx:beforeRequest` y reemplazarlas en `htmx:afterOnLoad`.
- **Archivos:** `layout.html` (CSS), `{entidad}s.html`

### 5. Breadcrumb dinámico con HTMX
- **Problema:** El breadcrumb está hardcodeado en cada template. Al navegar con HTMX se actualiza correctamente, pero si hay sub-secciones no refleja la ruta real.
- **Solución:** Pasar el contexto de breadcrumb desde el blueprint y renderizarlo dinámicamente en `_partial.html`.
- **Archivos:** `_partial.html`, blueprints

### 6. Paginación por defecto en DataTables
- **Problema:** Con muchos registros (ej: 200+ trabajadores), DataTable carga todo el DOM de una vez, lo que es lento.
- **Solución:** Configurar `pageLength: 10` y `lengthMenu: [10, 25, 50, 100]` como estándar en todos los DataTables.
- **Archivos:** `layout.html` (config global), `GUIA_MANTENEDORES.md`

### 7. Modal responsive en móvil
- **Problema:** Los modales usan `modal-xl` que en pantallas pequeñas queda mal recortado.
- **Solución:** Agregar clase `modal-fullscreen-sm-down` al div del modal en `layout.html`.
- **Archivos:** `layout.html`

---

## 🟢 Baja Prioridad
> Pulido y diferenciadores opcionales

### 8. Modo oscuro
- **Problema/Oportunidad:** El sistema pasa muchas horas en pantalla (turnos nocturnos). Un modo oscuro reduciría la fatiga visual.
- **Solución:** Toggle en el sidebar que aplica una clase `dark-mode` al `<body>`. Las variables CSS actuales facilitan esto. Persistir en `localStorage`.
- **Archivos:** `layout.html`, CSS global

### 9. Shortcuts de teclado
- **Oportunidad:** Para usuarios avanzados que usan el sistema intensivamente.
- **Atajos propuestos:**
  - `N` → Abrir modal "Agregar" en la página actual
  - `Escape` → Cerrar modal
  - `Ctrl+S` → Guardar formulario activo
- **Archivos:** `layout.html`

### 10. Indicador de registros inactivos
- **Problema:** La tabla muestra activos e inactivos mezclados. Es difícil distinguirlos visualmente más allá del badge.
- **Solución:** Filas inactivas con fondo levemente grisáceo (`table-secondary`) y opacidad reducida.
- **Archivos:** `partials/{entidad}_rows.html` (todos los partials)

### 11. Confirmación antes de cerrar modal con cambios
- **Problema:** Si el usuario llena el modal y hace click en "Cancelar" sin guardar, pierde los datos sin advertencia.
- **Solución:** Detectar si algún campo fue modificado (`change` event) y mostrar un `Swal.fire` de confirmación al hacer `CerrarModal()`.
- **Archivos:** `layout.html` (función `CerrarModal`)

---

## Notas de Implementación

- Implementar mejoras en orden de prioridad.
- Cada mejora debe respetar la **Regla de Renderizado** documentada en `PROJECT_CONTEXT.md`.
- Las mejoras de modales deben actualizarse también en `GUIA_MANTENEDORES.md`.
- Negociar con el usuario antes de implementar mejoras de baja prioridad.

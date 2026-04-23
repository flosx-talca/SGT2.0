# Avances y Roadmap del Proyecto SGT 2.1

Este documento sirve como bitácora central para documentar el progreso, definir el **Roadmap** de Features e Issues (los cuales se reflejarán en GitHub) y registrar el modelado de la base de datos a medida que se desarrolla la solución. 
Se basa directamente en `especificacion-funcional-sistema-turnos.md`.

---

## 🗺️ Roadmap de Desarrollo

*Nota: Todos los Features e Issues aquí listados deben ser negociados y aprobados con el usuario antes de su ejecución.*

### Fase 1: Integración con Base de Datos y Autenticación (Completada)
- [x] **Feature 1:** Conexión y Modelado Base de Datos PostgreSQL
- [x] **Feature 2:** Estandarización de Mantenedores a HTMX + PostgreSQL (Finalizado)
  - [x] Issue 2.1: Mantenedores de Geografía (Regiones/Comunas).
  - [x] Issue 2.2: Mantenedores de Operación (Feriados, Servicios, Turnos).
  - [x] Issue 2.3: Mantenedores de Estructura (Roles, Menús).
  - [x] Issue 2.4: Mantenedores de Negocio (Clientes, Empresas).
  - [x] Issue 2.5: Mantenedores de Personal y Seguridad (Trabajadores, Usuarios).

### Fase 2: Configuración de Negocio y Planificación (Siguiente)
- [ ] **Feature 3:** Motor de Reglas (REGLAS) - Lógica de cumplimiento legal y descansos.
- [ ] **Feature 4:** Cuadrante de Planificación - Interfaz de asignación de turnos.
- [ ] **Feature 5:** Autenticación Real - Sistema de Login funcional con Flask-Login.

---

## 📝 Bitácora de Avances
- **[2026-04-22]**: 
  - **Gran Migración**: Se completaron los 9 mantenedores principales del sistema bajo el estándar SGT 2.0.
  - **Arquitectura**: Desacoplamiento total mediante Blueprints dedicados por entidad.
  - **UX/UI**: Implementación de tarjetas premium para Turnos, refrescos parciales con HTMX (`_rows.html`) y Smart Spinner (delay 400ms).
  - **Personal y Seguridad**: Se mejoró radicalmente el mantenedor de **Trabajadores**, incluyendo ahora un sistema de gestión de **Preferencias de Turno** (Restricciones Duras) y **Ausencias/Permisos** (Vacaciones, Licencias).
  - **Integridad**: Validaciones de RUT, Email y campos obligatorios en todos los controladores.
  - **Motor de Reglas (Fase 2)**: 
    - Modelado en BD y SQLAlchemy de `Regla` (Reglas Maestras controladas por Super Admin) y `ReglaEmpresa` (Asignación personalizada por cliente).
    - Limpieza y Sincronización de Base de Datos: Se eliminaron tablas residuales (`regla_catalogo` y la antigua `regla_empresa`) para alinear correctamente la estructura PostgreSQL con los nuevos modelos SQLAlchemy.
    - Poblamiento Inicial de Reglas: Se creó el script `seed_reglas.py` y se insertaron las 6 reglas base de la legislación laboral chilena (Ley 21.561, reducción a 42 horas).
    - Creación de mantenedores con CRUD completo (`regla_bp` y `regla_empresa_bp`) adaptados al estándar SGT 2.1 con refresco parcial HTMX y modales dinámicos.
    - Estandarización de Interfaz: Se añadieron los contenedores tipo *Card*, bloques de títulos y *breadcrumbs* a los mantenedores de Reglas, igualando la estética de la vista de Trabajadores.
    - Corrección de Errores Críticos (Bugs): 
      - Se solucionó un problema de redeclaración de variables de inicialización de DataTables (`SyntaxError` con `let`) que rompía el buscador al navegar vía HTMX en toda la plataforma, reemplazándose por `var`.
      - Se corrigió un error interno en el modal de Empresas causado por una discrepancia de nombre de columna (`Comuna.nombre` por `Comuna.descripcion`), restableciendo su correcto funcionamiento.


  - **[2026-04-22 - Tipos de Ausencia Dinámicos]**: 
    - Se creó la entidad `TipoAusencia` para gestionar permisos, licencias y vacaciones desde la Base de Datos, eliminando dependencias de código estático.
    - Se añadió un mantenedor CRUD completo (`tipo_ausencia_bp.py`) con capacidad de definir la Sigla y el Color de la ausencia, integrado en el menú principal.
    - El formulario del Trabajador ahora carga estos motivos de manera dinámica, asignando el ID correcto a la tabla `TrabajadorAusencia`.
    - El simulador CP-SAT (`explain.py` y `simulacion.html`) fue optimizado para inyectar directamente la abreviación de la BD y pintar la celda usando el color configurado, logrando que el sistema escale sin necesidad de intervenir el código ante nuevos permisos.

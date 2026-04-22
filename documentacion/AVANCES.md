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


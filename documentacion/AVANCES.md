# Avances y Roadmap del Proyecto SGT 2.1

Este documento sirve como bitácora central para documentar el progreso, definir el **Roadmap** de Features e Issues (los cuales se reflejarán en GitHub) y registrar el modelado de la base de datos a medida que se desarrolla la solución. 
Se basa directamente en `especificacion-funcional-sistema-turnos.md`.

---

## 🗺️ Roadmap de Desarrollo

*Nota: Todos los Features e Issues aquí listados deben ser negociados y aprobados con el usuario antes de su ejecución.*

### Fase 1: Integración con Base de Datos y Autenticación (Actual)
- [x] **Feature 1:** Conexión y Modelado Base de Datos PostgreSQL
  - [x] Issue 1.1: Configuración de conexión y ORM (SQLAlchemy + psycopg2 + python-dotenv).
  - [x] Issue 1.2: Modelado completo de tablas (15 entidades en `proyecto.sql` y `app/models/`).
  - [x] Issue 1.3: Refactorización a arquitectura MVT (Application Factory + Blueprints).
  - [x] Issue 1.4: Creación de script `seed.py` con datos de prueba (4 Regiones, 7 Comunas, 3 Clientes, 4 Empresas, 5 Servicios, 10 Turnos, 11 Trabajadores).
  - [x] Issue 1.5: Regla de renderizado de frontend documentada en `PROJECT_CONTEXT.md` (datos antes de mostrar modal/tabla).
- [ ] **Feature 2:** Refactorización de Mantenedores a Base de Datos (En progreso)
  - [x] Issue 2.1: Mantenedor de Regiones (CRUD real contra PostgreSQL + Optimización HTMX).
  - [x] Issue 2.2: Mantenedor de Comunas.
  - [ ] Issue 2.3: Mantenedor de Feriados.
  - [ ] Issue 2.4: Mantenedor de Servicios.
  - [ ] Issue 2.5: Mantenedor de Empresas, Clientes y Usuarios.

### Fase 2: Configuración de Negocio (Multiempresa)
- [ ] **Feature 3:** Gestión de Trabajadores y Perfiles
- [ ] **Feature 4:** Motor de Reglas (REGLAS)
  - *Alta importancia: Requiere profundo análisis de la lógica de negocio.*

---

## 🗄️ Modelado de Base de Datos (Propuestas)

*Antes de crear cualquier tabla real en `proyecto.sql` o en el código, se propondrá aquí su estructura para revisión y observaciones del usuario.*

### Propuestas Actuales:
*(Esperando definición para iniciar con el modelo de Usuarios, Roles, Empresas...)*

---

## 📝 Bitácora de Avances
- **[2026-04-22]**: 
  - Se completó la migración de **Regiones** y **Comunas** a CRUD real con PostgreSQL.
  - Se implementó **Optimización HTMX**: Refresco parcial de tablas (tbody) y navegación tipo SPA (barra de progreso superior, carga de fragmentos de contenido).
  - Se establecieron índices en la BD para optimizar el rendimiento.
  - Se actualizó la `GUIA_MANTENEDORES.md` con el estándar de alto rendimiento.

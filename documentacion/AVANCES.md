# Avances y Roadmap del Proyecto SGT 2.1

Este documento sirve como bitácora central para documentar el progreso, definir el **Roadmap** de Features e Issues (los cuales se reflejarán en GitHub) y registrar el modelado de la base de datos a medida que se desarrolla la solución. 
Se basa directamente en `especificacion-funcional-sistema-turnos.md`.

---

## 🗺️ Roadmap de Desarrollo

*Nota: Todos los Features e Issues aquí listados deben ser negociados y aprobados con el usuario antes de su ejecución.*

### Fase 1: Integración con Base de Datos y Autenticación (Actual)
- [ ] **Feature 1:** Conexión y Modelado Base de Datos PostgreSQL
  - [ ] Issue 1.1: Configuración de conexión y ORM (SQLAlchemy) en Flask.
  - [ ] Issue 1.2: Modelado de tablas base (Empresas, Sucursales, Usuarios, Roles).
- [ ] **Feature 2:** Refactorización de Mantenedores a Base de Datos
  - [ ] Issue 2.1: Conectar Mantenedor de Regiones, Comunas y Feriados.
  - [ ] Issue 2.2: Conectar Mantenedor de Servicios.

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
- **[2026-04-22]**: Se crea la rama `IntegracionBD` para comenzar la migración de prototipos estáticos a una arquitectura conectada con PostgreSQL. Se establecen reglas estrictas en el contexto del proyecto respecto al modelado de datos, manejo de archivos `.env` y flujo de trabajo mediante Features e Issues.

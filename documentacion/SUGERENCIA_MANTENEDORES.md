# Informe: Sugerencia de Nuevos Mantenedores - SGT 2.1

Tras el análisis de los modelos de datos y los controladores actuales, se han identificado varios componentes críticos que carecen de una interfaz de gestión (CRUD). Implementar estos mantenedores permitirá una configuración más dinámica y profesional del sistema.

## 1. Gestión de Permisos (RolMenu)
**Modelo:** `RolMenu`
**Razón:** Actualmente, la relación entre un Rol y los Menús que puede visualizar está "atada" a lo que se inserte manualmente en la base de datos.
**Beneficio:** Permitiría al "Super Admin" activar o desactivar módulos enteros para ciertos tipos de usuarios (ej: ocultar 'Configuración' a los Supervisores) directamente desde la UI.

## 2. Plantillas de Configuración Base
**Modelos:** `TurnoPlantilla` y `TipoAusenciaPlantilla`
**Razón:** Para cada nueva empresa, hoy se deben crear los turnos desde cero.
**Beneficio:** Implementar un mantenedor de plantillas permitiría definir "Sets de Turnos" (ej: 'Retail Estándar', 'Seguridad 24/7') y clonarlos a nuevas empresas con un solo clic, acelerando drásticamente el Onboarding de clientes.

## 3. Auditoría de Cambios (CuadranteAuditoria)
**Modelo:** `CuadranteAuditoria`
**Razón:** El sistema ya registra quién cambia un turno generado por el Solver a uno manual, pero no hay donde ver este historial.
**Beneficio:** Daría transparencia total al "Cliente". Podría ver un reporte de: *"El usuario X cambió el turno del Trabajador Y el día Z por el motivo 'Emergencia familiar'"*.

## 4. Asignación Multi-Empresa (UsuarioEmpresa)
**Modelo:** `UsuarioEmpresa`
**Razón:** Aunque el modelo soporta que un usuario vea varias empresas, la asignación actual en `usuario_bp` es limitada.
**Beneficio:** Un mantenedor dedicado permitiría gestionar de forma masiva qué administradores tienen acceso a qué sucursales o empresas del holding.

## 5. Parámetros Legales Globales (COMPLETADO ✅)
**Modelo:** `ParametroLegal`
**Estado:** Ya existe el mantenedor funcional en `/parametros_legales`, restringido para el **Super Admin**.
**Valor:** Permite actualizar valores como la "Jornada Máxima Semanal" o "Umbral de Horas Extra" ante cambios en la legislación sin tocar código. Solo requiere asegurar que los parámetros clave estén cargados.

## 6. Autogestión de Administradores (Rol Cliente)
**Modelos:** `Usuario` y `UsuarioEmpresa`
**Razón:** Actualmente, la creación de usuarios con privilegios administrativos es una tarea que suele recaer en el Super Admin.
**Beneficio:** Permitiría que el usuario con rol **Cliente** (dueño de la cuenta) pueda crear sus propios "Administradores de Sucursal" y asignarles acceso a las empresas específicas que él decida, descentralizando la administración y mejorando los tiempos de respuesta operativos.

---
**Conclusión:**
La implementación de estos 6 mantenedores transformaría el SGT 2.1 de una herramienta de planificación a una **plataforma de gestión integral y auditable**, lista para escalabilidad multi-cliente.

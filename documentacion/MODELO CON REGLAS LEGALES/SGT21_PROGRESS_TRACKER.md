# SGT 2.1 — Seguimiento de Avances (Progress Tracker)

## 📋 Resumen de Implementación
Basado en la especificación técnica `sgt21_cursor_FINAL_v2.md`.

## 🛠️ Fase 1: Base de Datos y Modelos
- [x] **Paso 1: Modelos en `business.py`**
    - [x] Agregar entidad `ParametroLegal` (Parte 2.2)
    - [x] Agregar entidad `TrabajadorRestriccionTurno` (Parte 1.3)
    - [x] Migrar `Trabajador.tipo_contrato` a Enum `TipoContrato`
- [x] **Paso 2: Migraciones**
    - [x] Ejecutar `flask db migrate -m "add_parametro_legal_restriccion_turno"`
    - [x] Ejecutar `flask db upgrade`
- [x] **Paso 3: Enums y Constantes**
    - [x] Crear/Actualizar `app/models/enums.py` con `TipoContrato` y `RestrictionType`

## ⚙️ Fase 2: Servicios de Configuración y Lógica Legal
- [x] **Paso 4: ConfigManager (`app/services/config_manager.py`)**
    - [x] Implementar `preload()` para caché en memoria
    - [x] Implementar `get()`, `get_int()`, `get_bool()`
    - [x] Implementar `clear_cache()`
- [x] **Paso 5: LegalEngine (`app/services/legal_engine.py`)**
    - [x] Implementar cálculos de horas (Max semanal/diario)
    - [x] Implementar cálculos de días efectivos por turno
    - [x] Implementar lógica de domingos obligatorios (Art. 38)
    - [x] Implementar lógica de semanas cortas y prorrateo (Art. 28)
    - [x] Implementar función consolidada `resumen_legal(w, t, dias)`

## 🌱 Fase 3: Datos Iniciales (Seeds)
- [x] **Paso 6: Parámetros Legales (`app/seeds/parametros_legales.py`)**
    - [x] Catálogo de variables iniciales
    - [x] Ejecutar seed en base de datos
- [x] **Paso 7: Reglas Base (`app/seeds/reglas_base.py`)**
    - [x] Catálogo de 15 reglas iniciales
    - [x] Ejecutar seed en base de datos

## 🧠 Fase 4: Core del Solver (Builder)
- [x] **Paso 8: Builder (`app/scheduler/builder.py`)**
    - [x] Implementar `dividir_en_semanas` (detección automática de semanas cortas)
    - [x] Estructura `build_model` con precarga de `ConfigManager`
    - [x] Integrar restricciones de ausencias y especiales
    - [x] Implementar restricciones legales semanales usando `LegalEngine`
    - [x] Implementar **Estabilidad de Turno** (Parte 6.4)
- [x] **Paso 9: Orquestador (`app/services/scheduling_service.py`)**
    - [x] Mover lógica de negocio desde el controlador al servicio
    - [x] Implementar guardado atómico de asignaciones (Simulación lista)
    - [x] Implementar flujo completo: Fetch restricciones -> Resolver -> Guardar

## 🖥️ Fase 5: Interfaz de Usuario (UI)
- [x] **Paso 10: Modal de Restricciones Especiales**
    - [x] Implementar CRUD de `TrabajadorRestriccionTurno`
    - [x] Validaciones en tiempo real (`POST /api/restricciones/preview`)
    - [x] Interfaz de matriz (Día vs Turno)
- [x] **Paso 11: Mantenedor de Parámetros Legales**
    - [x] Interfaz para Super Admin para editar valores y activar/desactivar parámetros

## ✅ Validación Final
- [x] Test con empresa de prueba (período de 1 semana)
- [x] Verificar detección correcta de semanas cortas (inicio/fin de mes)
- [x] Verificar legibilidad del cuadrante (bloques estables de turno)

---
*Ultima actualización: 2026-04-27 (Implementación y Estabilización Completa)*

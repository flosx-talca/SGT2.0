-- proyecto.sql
-- Motor: PostgreSQL
-- Base de Datos: sgt

-- ==========================================
-- 1. REGION
-- ==========================================
CREATE TABLE IF NOT EXISTS region (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    descripcion VARCHAR(150) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_region_activo ON region(activo);
CREATE INDEX IF NOT EXISTS ix_region_codigo ON region(codigo);

-- ==========================================
-- 2. COMUNA
-- ==========================================
CREATE TABLE IF NOT EXISTS comuna (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    descripcion VARCHAR(150) NOT NULL,
    region_id INTEGER NOT NULL REFERENCES region(id) ON DELETE RESTRICT,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_comuna_activo ON comuna(activo);
CREATE INDEX IF NOT EXISTS ix_comuna_region_id ON comuna(region_id);

-- ==========================================
-- 3. ROL
-- ==========================================
CREATE TABLE IF NOT EXISTS rol (
    id SERIAL PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 4. MENU
-- ==========================================
CREATE TABLE IF NOT EXISTS menu (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para busquedas rapidas
CREATE INDEX idx_region_codigo ON region(codigo);
CREATE INDEX idx_comuna_codigo ON comuna(codigo);
CREATE INDEX idx_comuna_region ON comuna(region_id);

-- ==========================================
-- 5. CLIENTE (Holding / Dueño)
-- ==========================================
CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(15) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 6. EMPRESA (Local / Estación de servicio)
-- ==========================================
CREATE TABLE IF NOT EXISTS empresa (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(15) NOT NULL UNIQUE,
    razon_social VARCHAR(200) NOT NULL,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    comuna_id INTEGER NOT NULL REFERENCES comuna(id) ON DELETE RESTRICT,
    direccion VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 7. USUARIO (Acceso al sistema)
-- ==========================================
CREATE TABLE IF NOT EXISTS usuario (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(15) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES rol(id) ON DELETE RESTRICT,
    cliente_id INTEGER REFERENCES cliente(id) ON DELETE CASCADE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 8. FERIADO
-- ==========================================
CREATE TABLE IF NOT EXISTS feriado (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    es_regional BOOLEAN DEFAULT FALSE,
    region_id INTEGER REFERENCES region(id) ON DELETE CASCADE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, region_id) -- No repetir mismo feriado en misma región
);

-- Nuevos indices
CREATE INDEX idx_empresa_cliente ON empresa(cliente_id);
CREATE INDEX idx_usuario_cliente ON usuario(cliente_id);
CREATE INDEX idx_feriado_fecha ON feriado(fecha);

-- ==========================================
-- 9. SERVICIO (Tipo de Servicio Ej: Pronto, Pista)
-- ==========================================
CREATE TABLE IF NOT EXISTS servicio (
    id SERIAL PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL UNIQUE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 10. EMPRESA_SERVICIO (Muchos a Muchos)
-- ==========================================
CREATE TABLE IF NOT EXISTS empresa_servicio (
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    servicio_id INTEGER NOT NULL REFERENCES servicio(id) ON DELETE CASCADE,
    PRIMARY KEY (empresa_id, servicio_id)
);

-- ==========================================
-- 11. TRABAJADOR
-- ==========================================
CREATE TABLE IF NOT EXISTS trabajador (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(15) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido1 VARCHAR(100) NOT NULL,
    apellido2 VARCHAR(100),
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE RESTRICT,
    servicio_id INTEGER NOT NULL REFERENCES servicio(id) ON DELETE RESTRICT,
    cargo VARCHAR(100),
    email VARCHAR(150),
    telefono VARCHAR(20),
    tipo_contrato VARCHAR(50) NOT NULL DEFAULT 'full-time',
    horas_semanales INTEGER,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 12. TRABAJADOR_PREFERENCIA (Restricciones Duras)
-- ==========================================
CREATE TABLE IF NOT EXISTS trabajador_preferencia (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    dia_semana INTEGER NOT NULL CHECK (dia_semana >= 0 AND dia_semana <= 6),
    turno VARCHAR(5) NOT NULL,
    UNIQUE (trabajador_id, dia_semana, turno)
);

-- ==========================================
-- 13. TRABAJADOR_AUSENCIA (Vacaciones, Licencias)
-- ==========================================
CREATE TABLE IF NOT EXISTS trabajador_ausencia (
    id SERIAL PRIMARY KEY,
    trabajador_id INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    motivo VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices Fase 3
CREATE INDEX idx_trabajador_empresa ON trabajador(empresa_id);
CREATE INDEX idx_trabajador_servicio ON trabajador(servicio_id);
CREATE INDEX idx_ausencia_fechas ON trabajador_ausencia(fecha_inicio, fecha_fin);

-- ==========================================
-- 14. ROL_MENU (Permisos de Acceso)
-- ==========================================
CREATE TABLE IF NOT EXISTS rol_menu (
    rol_id INTEGER NOT NULL REFERENCES rol(id) ON DELETE CASCADE,
    menu_id INTEGER NOT NULL REFERENCES menu(id) ON DELETE CASCADE,
    puede_crear BOOLEAN DEFAULT FALSE,
    puede_editar BOOLEAN DEFAULT FALSE,
    puede_eliminar BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (rol_id, menu_id)
);

-- ==========================================
-- 15. TURNO
-- ==========================================
CREATE TABLE IF NOT EXISTS turno (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre VARCHAR(50) NOT NULL,
    abreviacion VARCHAR(5) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    color VARCHAR(10) DEFAULT '#18bc9c',
    dotacion_diaria INTEGER DEFAULT 1,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- ÍNDICES DE RENDIMIENTO
-- ==========================================
-- Índices globales para columnas de filtro frecuente
CREATE INDEX IF NOT EXISTS ix_turno_empresa     ON turno(empresa_id);
CREATE INDEX IF NOT EXISTS ix_turno_activo      ON turno(activo);
CREATE INDEX IF NOT EXISTS ix_trabajador_empresa ON trabajador(empresa_id);
CREATE INDEX IF NOT EXISTS ix_trabajador_activo  ON trabajador(activo);
CREATE INDEX IF NOT EXISTS ix_empresa_activo     ON empresa(activo);
CREATE INDEX IF NOT EXISTS ix_empresa_cliente    ON empresa(cliente_id);
CREATE INDEX IF NOT EXISTS ix_usuario_rol        ON usuario(rol_id);
CREATE INDEX IF NOT EXISTS ix_usuario_activo     ON usuario(activo);

-- ==========================================
-- 16. REGLA_FAMILIA (Motor genérico — familias de evaluación)
-- ==========================================
CREATE TABLE IF NOT EXISTS regla_familia (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(50)  NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo      BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_regla_familia_activo ON regla_familia(activo);
-- Valores de referencia: comparison, range, set_membership, sequence,
--   logic_all_any_not, calendar, worker_attribute, assignment_constraint

-- ==========================================
-- 17. REGLA_CATALOGO (Reglas globales — solo Super Admin)
-- ==========================================
CREATE TABLE IF NOT EXISTS regla_catalogo (
    id               SERIAL PRIMARY KEY,
    familia_id       INTEGER NOT NULL REFERENCES regla_familia(id) ON DELETE RESTRICT,
    codigo           VARCHAR(100) NOT NULL UNIQUE,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    rule_type        VARCHAR(20)  NOT NULL CHECK (rule_type IN ('hard','soft','client_rule','worker_restriction')),
    scope            VARCHAR(20)  NOT NULL CHECK (scope IN ('empresa','sucursal','area','trabajador')),
    field            VARCHAR(100),
    operator         VARCHAR(10),
    params_default   JSONB DEFAULT '{}'::jsonb,
    params_editables JSONB DEFAULT '[]'::jsonb,
    activo           BOOLEAN DEFAULT TRUE,
    creado_en        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_regla_catalogo_familia ON regla_catalogo(familia_id);
CREATE INDEX IF NOT EXISTS ix_regla_catalogo_activo  ON regla_catalogo(activo);
CREATE INDEX IF NOT EXISTS ix_regla_catalogo_tipo    ON regla_catalogo(rule_type);

-- ==========================================
-- 18. REGLA_EMPRESA (Instancias asignadas por Super Admin a empresas)
-- ==========================================
CREATE TABLE IF NOT EXISTS regla_empresa (
    id                 SERIAL PRIMARY KEY,
    regla_catalogo_id  INTEGER NOT NULL REFERENCES regla_catalogo(id) ON DELETE CASCADE,
    empresa_id         INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    params             JSONB DEFAULT '{}'::jsonb,
    is_enabled         BOOLEAN DEFAULT TRUE,
    creado_en          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_regla_empresa UNIQUE (regla_catalogo_id, empresa_id)
);
CREATE INDEX IF NOT EXISTS ix_regla_empresa_empresa   ON regla_empresa(empresa_id);
CREATE INDEX IF NOT EXISTS ix_regla_empresa_catalogo  ON regla_empresa(regla_catalogo_id);
CREATE INDEX IF NOT EXISTS ix_regla_empresa_enabled   ON regla_empresa(is_enabled);

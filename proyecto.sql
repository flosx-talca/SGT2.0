-- SGT 2.0 - Database Dump (Schema + Data)
-- Generated on: 2026-04-27 21:24:00.126578
SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

-- ############################################################
-- SCHEMA STRUCTURE
-- ############################################################

SET session_replication_role = 'replica'; -- Desactivar triggers/FKs temporalmente

-- Structure for table: region
DROP TABLE IF EXISTS region CASCADE;
CREATE TABLE region (
	id SERIAL NOT NULL, 
	codigo VARCHAR(10) NOT NULL, 
	descripcion VARCHAR(150) NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

-- Structure for table: comuna
DROP TABLE IF EXISTS comuna CASCADE;
CREATE TABLE comuna (
	id SERIAL NOT NULL, 
	codigo VARCHAR(20) NOT NULL, 
	descripcion VARCHAR(150) NOT NULL, 
	region_id INTEGER NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(region_id) REFERENCES region (id) ON DELETE RESTRICT
);

-- Structure for table: feriado
DROP TABLE IF EXISTS feriado CASCADE;
CREATE TABLE feriado (
	id SERIAL NOT NULL, 
	fecha DATE NOT NULL, 
	descripcion VARCHAR(200) NOT NULL, 
	es_regional BOOLEAN, 
	region_id INTEGER, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(region_id) REFERENCES region (id) ON DELETE CASCADE
);

-- Structure for table: rol
DROP TABLE IF EXISTS rol CASCADE;
CREATE TABLE rol (
	id SERIAL NOT NULL, 
	descripcion VARCHAR(100) NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (descripcion)
);

-- Structure for table: rol_menu
DROP TABLE IF EXISTS rol_menu CASCADE;
CREATE TABLE rol_menu (
	rol_id INTEGER NOT NULL, 
	menu_id INTEGER NOT NULL, 
	puede_crear BOOLEAN, 
	puede_editar BOOLEAN, 
	puede_eliminar BOOLEAN, 
	PRIMARY KEY (rol_id, menu_id), 
	FOREIGN KEY(rol_id) REFERENCES rol (id) ON DELETE CASCADE, 
	FOREIGN KEY(menu_id) REFERENCES menu (id) ON DELETE CASCADE
);

-- Structure for table: menu
DROP TABLE IF EXISTS menu CASCADE;
CREATE TABLE menu (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion VARCHAR(255), 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

-- Structure for table: usuario
DROP TABLE IF EXISTS usuario CASCADE;
CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	rut VARCHAR(15) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellidos VARCHAR(100) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	rol_id INTEGER NOT NULL, 
	cliente_id INTEGER, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (rut), 
	UNIQUE (email), 
	FOREIGN KEY(rol_id) REFERENCES rol (id) ON DELETE RESTRICT, 
	FOREIGN KEY(cliente_id) REFERENCES cliente (id) ON DELETE CASCADE
);

-- Structure for table: cliente
DROP TABLE IF EXISTS cliente CASCADE;
CREATE TABLE cliente (
	id SERIAL NOT NULL, 
	rut VARCHAR(15) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellidos VARCHAR(100) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (rut), 
	UNIQUE (email)
);

-- Structure for table: empresa
DROP TABLE IF EXISTS empresa CASCADE;
CREATE TABLE empresa (
	id SERIAL NOT NULL, 
	rut VARCHAR(15) NOT NULL, 
	razon_social VARCHAR(200) NOT NULL, 
	cliente_id INTEGER NOT NULL, 
	comuna_id INTEGER NOT NULL, 
	direccion VARCHAR(255) NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (rut), 
	FOREIGN KEY(cliente_id) REFERENCES cliente (id) ON DELETE RESTRICT, 
	FOREIGN KEY(comuna_id) REFERENCES comuna (id) ON DELETE RESTRICT
);

-- Structure for table: empresa_servicio
DROP TABLE IF EXISTS empresa_servicio CASCADE;
CREATE TABLE empresa_servicio (
	empresa_id INTEGER NOT NULL, 
	servicio_id INTEGER NOT NULL, 
	PRIMARY KEY (empresa_id, servicio_id), 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE CASCADE, 
	FOREIGN KEY(servicio_id) REFERENCES servicio (id) ON DELETE CASCADE
);

-- Structure for table: servicio
DROP TABLE IF EXISTS servicio CASCADE;
CREATE TABLE servicio (
	id SERIAL NOT NULL, 
	descripcion VARCHAR(100) NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (descripcion)
);

-- Structure for table: trabajador_ausencia
DROP TABLE IF EXISTS trabajador_ausencia CASCADE;
CREATE TABLE trabajador_ausencia (
	id SERIAL NOT NULL, 
	trabajador_id INTEGER NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE NOT NULL, 
	motivo VARCHAR(255) NOT NULL, 
	tipo_ausencia_id INTEGER, 
	restriccion_id INTEGER, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(trabajador_id) REFERENCES trabajador (id) ON DELETE CASCADE, 
	FOREIGN KEY(tipo_ausencia_id) REFERENCES tipo_ausencia (id) ON DELETE CASCADE, 
	FOREIGN KEY(restriccion_id) REFERENCES trabajador_restriccion_turno (id)
);

-- Structure for table: turno
DROP TABLE IF EXISTS turno CASCADE;
CREATE TABLE turno (
	id SERIAL NOT NULL, 
	empresa_id INTEGER NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	abreviacion VARCHAR(5) NOT NULL, 
	hora_inicio TIME WITHOUT TIME ZONE NOT NULL, 
	hora_fin TIME WITHOUT TIME ZONE NOT NULL, 
	color VARCHAR(10), 
	dotacion_diaria INTEGER, 
	es_nocturno BOOLEAN NOT NULL, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE CASCADE
);

-- Structure for table: trabajador_preferencia
DROP TABLE IF EXISTS trabajador_preferencia CASCADE;
CREATE TABLE trabajador_preferencia (
	id SERIAL NOT NULL, 
	trabajador_id INTEGER NOT NULL, 
	dia_semana INTEGER NOT NULL, 
	turno VARCHAR(5) NOT NULL, 
	tipo VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(trabajador_id) REFERENCES trabajador (id) ON DELETE CASCADE
);

-- Structure for table: regla_empresa
DROP TABLE IF EXISTS regla_empresa CASCADE;
CREATE TABLE regla_empresa (
	id SERIAL NOT NULL, 
	empresa_id INTEGER NOT NULL, 
	regla_id INTEGER NOT NULL, 
	params_custom JSON, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE CASCADE, 
	FOREIGN KEY(regla_id) REFERENCES regla (id) ON DELETE CASCADE
);

-- Structure for table: regla
DROP TABLE IF EXISTS regla CASCADE;
CREATE TABLE regla (
	id SERIAL NOT NULL, 
	codigo VARCHAR(50) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	familia VARCHAR(50) NOT NULL, 
	tipo_regla VARCHAR(20) NOT NULL, 
	scope VARCHAR(50) NOT NULL, 
	campo VARCHAR(100), 
	operador VARCHAR(20), 
	params_base JSON, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

-- Structure for table: tipo_ausencia
DROP TABLE IF EXISTS tipo_ausencia CASCADE;
CREATE TABLE tipo_ausencia (
	id SERIAL NOT NULL, 
	empresa_id INTEGER NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	abreviacion VARCHAR(5) NOT NULL, 
	color VARCHAR(10), 
	categoria categoriaausencia NOT NULL, 
	tipo_restriccion VARCHAR(30), 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE CASCADE
);

-- Structure for table: trabajador
DROP TABLE IF EXISTS trabajador CASCADE;
CREATE TABLE trabajador (
	id SERIAL NOT NULL, 
	rut VARCHAR(15) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellido1 VARCHAR(100) NOT NULL, 
	apellido2 VARCHAR(100), 
	empresa_id INTEGER NOT NULL, 
	servicio_id INTEGER NOT NULL, 
	cargo VARCHAR(100), 
	email VARCHAR(150), 
	telefono VARCHAR(20), 
	tipo_contrato tipocontrato NOT NULL, 
	horas_semanales INTEGER NOT NULL, 
	permite_horas_extra BOOLEAN, 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (rut), 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE RESTRICT, 
	FOREIGN KEY(servicio_id) REFERENCES servicio (id) ON DELETE RESTRICT
);

-- Structure for table: trabajador_restriccion_turno
DROP TABLE IF EXISTS trabajador_restriccion_turno CASCADE;
CREATE TABLE trabajador_restriccion_turno (
	id SERIAL NOT NULL, 
	trabajador_id INTEGER NOT NULL, 
	empresa_id INTEGER NOT NULL, 
	tipo VARCHAR(30) NOT NULL, 
	naturaleza VARCHAR(10) NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE NOT NULL, 
	dias_semana JSON, 
	turno_id INTEGER, 
	turno_alternativo_id INTEGER, 
	motivo VARCHAR(200), 
	activo BOOLEAN, 
	creado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(trabajador_id) REFERENCES trabajador (id) ON DELETE CASCADE, 
	FOREIGN KEY(empresa_id) REFERENCES empresa (id) ON DELETE CASCADE, 
	FOREIGN KEY(turno_id) REFERENCES turno (id) ON DELETE RESTRICT, 
	FOREIGN KEY(turno_alternativo_id) REFERENCES turno (id) ON DELETE RESTRICT
);

-- Structure for table: parametro_legal
DROP TABLE IF EXISTS parametro_legal CASCADE;
CREATE TABLE parametro_legal (
	id SERIAL NOT NULL, 
	codigo VARCHAR(60) NOT NULL, 
	valor FLOAT NOT NULL, 
	categoria VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(255), 
	es_activo BOOLEAN DEFAULT TRUE NOT NULL, 
	es_obligatorio BOOLEAN DEFAULT TRUE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

-- Structure for table: turno_plantilla
DROP TABLE IF EXISTS turno_plantilla CASCADE;
CREATE TABLE turno_plantilla (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    abreviacion VARCHAR(5) UNIQUE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    color VARCHAR(10),
    dotacion_diaria INTEGER DEFAULT 1,
    es_nocturno BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Structure for table: tipo_ausencia_plantilla
DROP TABLE IF EXISTS tipo_ausencia_plantilla CASCADE;
CREATE TABLE tipo_ausencia_plantilla (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    abreviacion VARCHAR(5) UNIQUE NOT NULL,
    color VARCHAR(10),
    categoria VARCHAR(20) NOT NULL,
    tipo_restriccion VARCHAR(30),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ############################################################
-- DATA CONTENT
-- ############################################################

-- Dumping data for: region
INSERT INTO "region" ("id", "codigo", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (1, 'RM', 'Región Metropolitana', True, '2026-04-23 14:00:03.582415', '2026-04-23 14:00:03.582419');

-- Dumping data for: comuna
INSERT INTO "comuna" ("id", "codigo", "descripcion", "region_id", "activo", "creado_en", "actualizado_en") VALUES (1, 'STGO', 'Santiago', 1, True, '2026-04-23 14:00:03.587558', '2026-04-23 14:00:03.587560');

-- Dumping data for: feriado
INSERT INTO "feriado" ("id", "fecha", "descripcion", "es_regional", "region_id", "activo", "creado_en", "actualizado_en") VALUES (1, '2025-01-01', 'Año Nuevo', False, NULL, True, '2026-04-23 14:00:03.591189', '2026-04-23 14:00:03.591193');

-- Dumping data for: rol
INSERT INTO "rol" ("id", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (1, 'Super Admin', True, '2026-04-23 14:00:03.593688', '2026-04-23 14:00:03.593690');

-- Dumping data for: rol_menu

-- Dumping data for: menu
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (1, 'Dashboard', NULL, True, '2026-04-23 14:00:03.596100', '2026-04-23 14:00:03.596102');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (2, 'Trabajadores', NULL, True, '2026-04-23 14:00:03.596104', '2026-04-23 14:00:03.596105');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (3, 'Turnos', NULL, True, '2026-04-23 14:00:03.596106', '2026-04-23 14:00:03.596107');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (4, 'Planificación', NULL, True, '2026-04-23 14:00:03.596108', '2026-04-23 14:00:03.596109');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (5, 'Clientes', NULL, True, '2026-04-23 14:00:03.596110', '2026-04-23 14:00:03.596111');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (6, 'Usuarios', NULL, True, '2026-04-23 14:00:03.596113', '2026-04-23 14:00:03.596114');
INSERT INTO "menu" ("id", "nombre", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (7, 'Empresas', NULL, True, '2026-04-23 14:00:03.596115', '2026-04-23 14:00:03.596116');

-- Dumping data for: usuario
INSERT INTO "usuario" ("id", "rut", "nombre", "apellidos", "email", "password_hash", "rol_id", "cliente_id", "activo", "creado_en", "actualizado_en") VALUES (1, '99999999-9', 'Admin', 'Sistema', 'admin@sgt.cl', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 1, NULL, True, '2026-04-23 14:00:03.622643', '2026-04-23 14:00:03.622646');

-- Dumping data for: cliente
INSERT INTO "cliente" ("id", "rut", "nombre", "apellidos", "email", "activo", "creado_en", "actualizado_en") VALUES (1, '11111111-1', 'Admin', 'SGT', 'contacto@sgt.cl', True, '2026-04-23 14:00:03.598242', '2026-04-23 14:00:03.598244');

-- Dumping data for: empresa
INSERT INTO "empresa" ("id", "rut", "razon_social", "cliente_id", "comuna_id", "direccion", "activo", "creado_en", "actualizado_en") VALUES (1, '76111111-1', 'Empresa Demo SGT', 1, 1, 'Av. Principal 123', True, '2026-04-23 14:00:03.602016', '2026-04-23 14:00:03.602018');

-- Dumping data for: empresa_servicio
INSERT INTO "empresa_servicio" ("empresa_id", "servicio_id") VALUES (1, 1);
INSERT INTO "empresa_servicio" ("empresa_id", "servicio_id") VALUES (1, 2);

-- Dumping data for: servicio
INSERT INTO "servicio" ("id", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (1, 'Pista Combustible', True, '2026-04-23 14:00:03.604051', '2026-04-23 14:00:03.604054');
INSERT INTO "servicio" ("id", "descripcion", "activo", "creado_en", "actualizado_en") VALUES (2, 'Tienda Pronto', True, '2026-04-23 14:00:03.604055', '2026-04-23 14:00:03.604056');

-- Dumping data for: trabajador_ausencia
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (4, 1, '2026-04-24', '2026-04-27', 'vacaciones', 1, '2026-04-24 14:10:02.771885', NULL);
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (5, 7, '2026-05-01', '2026-05-24', '', 2, '2026-04-24 17:11:05.150640', NULL);
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (6, 1, '2026-05-01', '2026-05-31', 'test', 9, '2026-04-27 21:58:55.438616', NULL);
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (9, 2, '2026-05-01', '2026-05-31', 'prrueba de LM', 2, '2026-04-27 22:25:59.496521', NULL);
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (11, 2, '2026-04-29', '2026-04-30', '', 8, '2026-04-27 22:27:38.022428', 5);
INSERT INTO "trabajador_ausencia" ("id", "trabajador_id", "fecha_inicio", "fecha_fin", "motivo", "tipo_ausencia_id", "creado_en", "restriccion_id") VALUES (12, 2, '2026-04-27', '2026-04-28', '', 3, '2026-04-27 22:27:38.022433', NULL);

-- Dumping data for: turno
INSERT INTO "turno" ("id", "empresa_id", "nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "dotacion_diaria", "activo", "creado_en", "actualizado_en", "es_nocturno") VALUES (1, 1, 'MAÑANA', 'M', '07:00:00', '15:00:00', '#3498db', 2, True, '2026-04-23 14:00:03.613762', '2026-04-23 14:34:30.079648', False);
INSERT INTO "turno" ("id", "empresa_id", "nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "dotacion_diaria", "activo", "creado_en", "actualizado_en", "es_nocturno") VALUES (4, 1, 'INTERMEDIO', 'I', '11:00:00', '19:00:00', '#1abc9c', 1, True, '2026-04-23 14:00:03.613770', '2026-04-23 14:35:18.639575', False);
INSERT INTO "turno" ("id", "empresa_id", "nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "dotacion_diaria", "activo", "creado_en", "actualizado_en", "es_nocturno") VALUES (2, 1, 'TARDE', 'T', '15:00:00', '23:00:00', '#e67e22', 2, True, '2026-04-23 14:00:03.613766', '2026-04-23 14:35:25.767022', False);
INSERT INTO "turno" ("id", "empresa_id", "nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "dotacion_diaria", "activo", "creado_en", "actualizado_en", "es_nocturno") VALUES (3, 1, 'NOCHE', 'N', '23:00:00', '07:00:00', '#2c3e50', 1, True, '2026-04-23 14:00:03.613768', '2026-04-23 14:35:12.231063', True);
INSERT INTO "turno" ("id", "empresa_id", "nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "dotacion_diaria", "activo", "creado_en", "actualizado_en", "es_nocturno") VALUES (5, 1, 'TEST', 'T1', '16:58:00', '17:59:00', '#18bc9c', 2, False, '2026-04-27 20:58:43.048781', '2026-04-27 20:59:22.815046', False);

-- Dumping data for: trabajador_preferencia
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (120, 2, 0, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (121, 2, 1, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (122, 2, 2, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (123, 2, 3, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (124, 2, 4, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (125, 2, 5, 'N', 'solo_turno');
INSERT INTO "trabajador_preferencia" ("id", "trabajador_id", "dia_semana", "turno", "tipo") VALUES (126, 2, 6, 'N', 'solo_turno');

-- Dumping data for: regla_empresa

-- Dumping data for: regla
INSERT INTO "regla" ("id", "codigo", "nombre", "familia", "tipo_regla", "scope", "campo", "operador", "params_base", "activo", "creado_en", "actualizado_en") VALUES (1, 'dias_descanso_post_6', 'Días de descanso tras 6 días trabajados', 'descanso', 'hard', 'empresa', 'dias_descanso', 'gte', '{"value": 1}'::jsonb, True, '2026-04-23 15:08:58.467858', '2026-04-23 15:08:58.467858');
INSERT INTO "regla" ("id", "codigo", "nombre", "familia", "tipo_regla", "scope", "campo", "operador", "params_base", "activo", "creado_en", "actualizado_en") VALUES (2, 'jornada_semanal', 'Jornada semanal por defecto (horas)', 'contrato', 'hard', 'empresa', 'horas_semanales', 'eq', '{"value": 42}'::jsonb, True, '2026-04-23 15:08:58.467858', '2026-04-23 15:08:58.467858');
INSERT INTO "regla" ("id", "codigo", "nombre", "familia", "tipo_regla", "scope", "campo", "operador", "params_base", "activo", "creado_en", "actualizado_en") VALUES (3, 'duracion_turno', 'Duración estándar del turno (horas)', 'contrato', 'hard', 'empresa', 'duracion_turno', 'eq', '{"value": 8}'::jsonb, True, '2026-04-23 15:08:58.467858', '2026-04-23 15:08:58.467858');

-- Dumping data for: tipo_ausencia
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (2, 1, 'Licencia medica', 'LM', '#f01c05', True, '2026-04-24 17:07:40.128377', '2026-04-24 17:07:40.128380', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (1, 1, 'vacaciones', 'V', '#7be740', True, '2026-04-23 14:13:37.134408', '2026-04-24 17:07:54.739666', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (3, 1, 'Vacaciones', 'VAC', '#3498db', True, '2026-04-27 21:55:04.974755', '2026-04-27 21:55:04.974758', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (4, 1, 'Permiso con goce', 'PCG', '#f39c12', True, '2026-04-27 21:55:04.976726', '2026-04-27 21:55:04.976728', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (5, 1, 'Permiso sin goce', 'PSG', '#95a5a6', True, '2026-04-27 21:55:04.977480', '2026-04-27 21:55:04.977481', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (6, 1, 'Día compensatorio', 'COMP', '#9b59b6', True, '2026-04-27 21:55:04.978165', '2026-04-27 21:55:04.978167', 'AUSENCIA', NULL);
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (7, 1, 'Turno fijo', 'TF', '#27ae60', True, '2026-04-27 21:55:04.978847', '2026-04-27 21:55:04.978849', 'RESTRICCION', 'turno_fijo');
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (8, 1, 'Excluir turno', 'ET', '#c0392b', True, '2026-04-27 21:55:04.979505', '2026-04-27 21:55:04.979507', 'RESTRICCION', 'excluir_turno');
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (9, 1, 'Solo turno', 'ST', '#2980b9', True, '2026-04-27 21:55:04.980223', '2026-04-27 21:55:04.980226', 'RESTRICCION', 'solo_turno');
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (10, 1, 'Turno preferente', 'TP', '#f1c40f', True, '2026-04-27 21:55:04.980891', '2026-04-27 21:55:04.980893', 'RESTRICCION', 'turno_preferente');
INSERT INTO "tipo_ausencia" ("id", "empresa_id", "nombre", "abreviacion", "color", "activo", "creado_en", "actualizado_en", "categoria", "tipo_restriccion") VALUES (11, 1, 'Post noche libre', 'PNL', '#1abc9c', True, '2026-04-27 21:55:04.981423', '2026-04-27 21:55:04.981425', 'RESTRICCION', 'post_noche');

-- Dumping data for: trabajador
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (7, '157742477', 'Orlando', 'Rozas', 'Rozas', 1, 1, 'sasdasd', 'orlandorozasi@gmail.com', '0984530346', 'PART_TIME_30', 30, True, '2026-04-24 16:10:10.594545', '2026-04-24 18:51:34.014272', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (2, '10100002-2', 'Ana', 'Torres', 'None', 1, 1, 'Operario', 'ana@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618778', '2026-04-24 19:03:57.433829', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (1, '10100001-1', 'Carlos', 'Muñoz', 'None', 1, 1, 'Operario', 'carlos@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618774', '2026-04-23 14:04:53.538637', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (3, '10100003-3', 'Diego', 'Salinas', 'None', 1, 1, 'Cajero', 'diego@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618780', '2026-04-23 14:00:53.725874', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (4, '10100004-4', 'Valentina', 'Reyes', 'None', 1, 1, 'Cajero', 'valentina@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618783', '2026-04-23 14:00:58.967530', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (5, '10100005-5', 'Felipe', 'Contreras', 'None', 1, 1, 'Operario', 'felipe@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618785', '2026-04-23 19:55:56.807275', True);
INSERT INTO "trabajador" ("id", "rut", "nombre", "apellido1", "apellido2", "empresa_id", "servicio_id", "cargo", "email", "telefono", "tipo_contrato", "horas_semanales", "activo", "creado_en", "actualizado_en", "permite_horas_extra") VALUES (6, '10100006-6', 'Claudia', 'Fernández', 'None', 1, 1, 'Cajera', 'claudia@sgt.cl', 'None', 'FULL_TIME', 42, True, '2026-04-23 14:00:03.618787', '2026-04-23 14:00:48.656939', True);

-- Dumping data for: alembic_version
INSERT INTO "alembic_version" ("version_num") VALUES ('c18184e4a3f7');

-- Dumping data for: trabajador_restriccion_turno
INSERT INTO "trabajador_restriccion_turno" ("id", "trabajador_id", "empresa_id", "tipo", "naturaleza", "fecha_inicio", "fecha_fin", "dias_semana", "turno_id", "turno_alternativo_id", "motivo", "activo", "creado_en") VALUES (1, 2, 1, 'turno_fijo', 'hard', '2026-05-01', '2026-05-31', '[0, 3, 6]'::jsonb, 1, NULL, 'prueba turno fijo', True, '2026-04-27 21:43:11.931440');
INSERT INTO "trabajador_restriccion_turno" ("id", "trabajador_id", "empresa_id", "tipo", "naturaleza", "fecha_inicio", "fecha_fin", "dias_semana", "turno_id", "turno_alternativo_id", "motivo", "activo", "creado_en") VALUES (2, 1, 1, 'solo_turno', 'hard', '2026-05-01', '2026-05-31', '[1]'::jsonb, 1, NULL, 'test', True, '2026-04-27 21:58:55.440392');
INSERT INTO "trabajador_restriccion_turno" ("id", "trabajador_id", "empresa_id", "tipo", "naturaleza", "fecha_inicio", "fecha_fin", "dias_semana", "turno_id", "turno_alternativo_id", "motivo", "activo", "creado_en") VALUES (5, 2, 1, 'excluir_turno', 'hard', '2026-04-29', '2026-04-30', '[0, 1, 2, 3, 4, 5, 6]'::jsonb, 2, NULL, '', True, '2026-04-27 22:27:38.020629');

-- Dumping data for: parametro_legal
INSERT INTO "parametro_legal" ("codigo", "valor", "categoria", "descripcion") VALUES ('MAX_HRS_SEMANA_FULL', 42.0, 'Jornada', 'Horas semanales máximas (Ley 21.561)');
INSERT INTO "parametro_legal" ("codigo", "valor", "categoria", "descripcion") VALUES ('W_DEFICIT', 10000000.0, 'Optimizacion', 'Penalización por turno no cubierto');
INSERT INTO "parametro_legal" ("codigo", "valor", "categoria", "descripcion") VALUES ('W_EXCESO_HORAS', 20000000.0, 'Optimizacion', 'Penalización por exceso de jornada semanal');
INSERT INTO "parametro_legal" ("codigo", "valor", "categoria", "descripcion") VALUES ('W_META', 50000.0, 'Optimizacion', 'Penalización por desviación de la meta mensual');

-- Dumping data for: turno_plantilla
INSERT INTO "turno_plantilla" ("nombre", "abreviacion", "hora_inicio", "hora_fin", "color") VALUES ('Mañana', 'M', '07:00:00', '15:00:00', '#18bc9c');
INSERT INTO "turno_plantilla" ("nombre", "abreviacion", "hora_inicio", "hora_fin", "color") VALUES ('Tarde', 'T', '15:00:00', '23:00:00', '#3498db');
INSERT INTO "turno_plantilla" ("nombre", "abreviacion", "hora_inicio", "hora_fin", "color", "es_nocturno") VALUES ('Noche', 'N', '23:00:00', '07:00:00', '#34495e', True);

-- Dumping data for: tipo_ausencia_plantilla
INSERT INTO "tipo_ausencia_plantilla" ("nombre", "abreviacion", "color", "categoria") VALUES ('Vacaciones', 'VAC', '#2ecc71', 'ausencia');
INSERT INTO "tipo_ausencia_plantilla" ("nombre", "abreviacion", "color", "categoria") VALUES ('Licencia Médica', 'LIC', '#e74c3c', 'ausencia');
INSERT INTO "tipo_ausencia_plantilla" ("nombre", "abreviacion", "color", "categoria", "tipo_restriccion") VALUES ('Turno Fijo', 'TFIJ', '#f1c40f', 'restriccion', 'turno_fijo');
INSERT INTO "tipo_ausencia_plantilla" ("nombre", "abreviacion", "color", "categoria", "tipo_restriccion") VALUES ('Solo este Turno', 'SOLO', '#3498db', 'restriccion', 'solo_turno');

SET session_replication_role = 'origin'; -- Reactivar triggers/FKs

-- Migracion Feriados
ALTER TABLE "feriado" ADD COLUMN "es_irrenunciable" BOOLEAN DEFAULT FALSE;
ALTER TABLE "feriado" ADD COLUMN "tipo" VARCHAR(20) DEFAULT 'nacional';
ALTER TABLE "feriado" ADD COLUMN "fuente" VARCHAR(50) DEFAULT 'feriados.io';
ALTER TABLE "feriado" ADD COLUMN "regiones" VARCHAR(100);
CREATE INDEX "idx_feriado_fecha" ON "feriado" ("fecha");
CREATE INDEX "idx_feriado_activo" ON "feriado" ("activo", "fecha");
-- MIGRACIÓN CUADRANTE --
CREATE TABLE IF NOT EXISTS cuadrante_cabecera (
    id                    SERIAL PRIMARY KEY,
    empresa_id            INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    sucursal_id           INTEGER NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    servicio_id           INTEGER REFERENCES servicio(id) ON DELETE SET NULL,
    mes                   SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio                  SMALLINT NOT NULL CHECK (anio >= 2024),
    estado                VARCHAR(20) NOT NULL DEFAULT 'guardado'
                          CHECK (estado IN ('guardado', 'cerrado')),
    generado_por_user_id  INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    generado_en           TIMESTAMP DEFAULT NOW(),
    guardado_por_user_id  INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    guardado_en           TIMESTAMP,
    creado_en             TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_cuadrante_periodo UNIQUE (sucursal_id, servicio_id, mes, anio)
);

CREATE INDEX IF NOT EXISTS idx_cab_empresa ON cuadrante_cabecera(empresa_id, anio, mes);
CREATE INDEX IF NOT EXISTS idx_cab_sucursal ON cuadrante_cabecera(sucursal_id, anio, mes);

CREATE TABLE IF NOT EXISTS cuadrante_asignacion (
    id                       SERIAL PRIMARY KEY,
    cabecera_id              INTEGER NOT NULL REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    trabajador_id            INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    fecha                    DATE NOT NULL,
    turno_id                 INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    es_libre                 BOOLEAN NOT NULL DEFAULT FALSE,
    horas_asignadas          NUMERIC(4,2) DEFAULT 0,
    origen                   VARCHAR(10) NOT NULL DEFAULT 'solver'
                             CHECK (origen IN ('solver', 'manual')),
    modificado_por_user_id   INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    modificado_en            TIMESTAMP,
    es_feriado               BOOLEAN DEFAULT FALSE,
    es_domingo               BOOLEAN DEFAULT FALSE,
    es_irrenunciable         BOOLEAN DEFAULT FALSE,
    es_feriado_regional      BOOLEAN DEFAULT FALSE,
    tipo_dia                 VARCHAR(30) DEFAULT 'normal',
    CONSTRAINT uq_asignacion_trabajador_fecha UNIQUE (cabecera_id, trabajador_id, fecha)
);

CREATE INDEX IF NOT EXISTS idx_asig_cabecera ON cuadrante_asignacion(cabecera_id);
CREATE INDEX IF NOT EXISTS idx_asig_trabajador ON cuadrante_asignacion(trabajador_id, fecha);
CREATE INDEX IF NOT EXISTS idx_asig_origen ON cuadrante_asignacion(origen);

CREATE TABLE IF NOT EXISTS cuadrante_auditoria (
    id                  SERIAL PRIMARY KEY,
    asignacion_id       INTEGER NOT NULL REFERENCES cuadrante_asignacion(id) ON DELETE CASCADE,
    cabecera_id         INTEGER NOT NULL REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    user_id             INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    fecha_cambio        TIMESTAMP NOT NULL DEFAULT NOW(),
    turno_anterior_id   INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    turno_nuevo_id      INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    era_libre_antes     BOOLEAN DEFAULT FALSE,
    es_libre_ahora      BOOLEAN DEFAULT FALSE,
    ip_address          VARCHAR(45),
    motivo              VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_aud_asignacion ON cuadrante_auditoria(asignacion_id);
CREATE INDEX IF NOT EXISTS idx_aud_user ON cuadrante_auditoria(user_id, fecha_cambio DESC);
CREATE INDEX IF NOT EXISTS idx_aud_cabecera ON cuadrante_auditoria(cabecera_id, fecha_cambio DESC);

-- MIGRACIÓN CUADRANTE --
CREATE TABLE IF NOT EXISTS cuadrante_cabecera (
    id                    SERIAL PRIMARY KEY,
    empresa_id            INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    servicio_id           INTEGER REFERENCES servicio(id) ON DELETE SET NULL,
    mes                   SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio                  SMALLINT NOT NULL CHECK (anio >= 2024),
    estado                VARCHAR(20) NOT NULL DEFAULT 'guardado'
                          CHECK (estado IN ('guardado', 'cerrado')),
    generado_por_user_id  INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    generado_en           TIMESTAMP DEFAULT NOW(),
    guardado_por_user_id  INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    guardado_en           TIMESTAMP,
    creado_en             TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_cuadrante_periodo UNIQUE (empresa_id, servicio_id, mes, anio)
);

CREATE INDEX IF NOT EXISTS idx_cab_empresa ON cuadrante_cabecera(empresa_id, anio, mes);

CREATE TABLE IF NOT EXISTS cuadrante_asignacion (
    id                       SERIAL PRIMARY KEY,
    cabecera_id              INTEGER NOT NULL REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    trabajador_id            INTEGER NOT NULL REFERENCES trabajador(id) ON DELETE CASCADE,
    fecha                    DATE NOT NULL,
    turno_id                 INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    es_libre                 BOOLEAN NOT NULL DEFAULT FALSE,
    horas_asignadas          NUMERIC(4,2) DEFAULT 0,
    origen                   VARCHAR(10) NOT NULL DEFAULT 'solver'
                             CHECK (origen IN ('solver', 'manual')),
    modificado_por_user_id   INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    modificado_en            TIMESTAMP,
    es_feriado               BOOLEAN DEFAULT FALSE,
    es_domingo               BOOLEAN DEFAULT FALSE,
    es_irrenunciable         BOOLEAN DEFAULT FALSE,
    es_feriado_regional      BOOLEAN DEFAULT FALSE,
    tipo_dia                 VARCHAR(30) DEFAULT 'normal',
    CONSTRAINT uq_asignacion_trabajador_fecha UNIQUE (cabecera_id, trabajador_id, fecha)
);

CREATE INDEX IF NOT EXISTS idx_asig_cabecera ON cuadrante_asignacion(cabecera_id);
CREATE INDEX IF NOT EXISTS idx_asig_trabajador ON cuadrante_asignacion(trabajador_id, fecha);
CREATE INDEX IF NOT EXISTS idx_asig_origen ON cuadrante_asignacion(origen);

CREATE TABLE IF NOT EXISTS cuadrante_auditoria (
    id                  SERIAL PRIMARY KEY,
    asignacion_id       INTEGER NOT NULL REFERENCES cuadrante_asignacion(id) ON DELETE CASCADE,
    cabecera_id         INTEGER NOT NULL REFERENCES cuadrante_cabecera(id) ON DELETE CASCADE,
    user_id             INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    fecha_cambio        TIMESTAMP NOT NULL DEFAULT NOW(),
    turno_anterior_id   INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    turno_nuevo_id      INTEGER REFERENCES turno(id) ON DELETE SET NULL,
    era_libre_antes     BOOLEAN DEFAULT FALSE,
    es_libre_ahora      BOOLEAN DEFAULT FALSE,
    ip_address          VARCHAR(45),
    motivo              VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_aud_asignacion ON cuadrante_auditoria(asignacion_id);
CREATE INDEX IF NOT EXISTS idx_aud_user ON cuadrante_auditoria(user_id, fecha_cambio DESC);
CREATE INDEX IF NOT EXISTS idx_aud_cabecera ON cuadrante_auditoria(cabecera_id, fecha_cambio DESC);


--
-- PostgreSQL database dump
--

-- Dumped from database version 15.2
-- Dumped by pg_dump version 15.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_rol_id_fkey;
ALTER TABLE IF EXISTS ONLY public.usuario_empresa DROP CONSTRAINT IF EXISTS usuario_empresa_usuario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.usuario_empresa DROP CONSTRAINT IF EXISTS usuario_empresa_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_empresa_activa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_cliente_id_fkey;
ALTER TABLE IF EXISTS ONLY public.turno DROP CONSTRAINT IF EXISTS turno_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador DROP CONSTRAINT IF EXISTS trabajador_servicio_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_restriccion_turno DROP CONSTRAINT IF EXISTS trabajador_restriccion_turno_turno_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_restriccion_turno DROP CONSTRAINT IF EXISTS trabajador_restriccion_turno_turno_alternativo_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_restriccion_turno DROP CONSTRAINT IF EXISTS trabajador_restriccion_turno_trabajador_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_restriccion_turno DROP CONSTRAINT IF EXISTS trabajador_restriccion_turno_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_preferencia DROP CONSTRAINT IF EXISTS trabajador_preferencia_trabajador_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador DROP CONSTRAINT IF EXISTS trabajador_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_ausencia DROP CONSTRAINT IF EXISTS trabajador_ausencia_trabajador_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_ausencia DROP CONSTRAINT IF EXISTS trabajador_ausencia_tipo_ausencia_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_ausencia DROP CONSTRAINT IF EXISTS trabajador_ausencia_restriccion_id_fkey;
ALTER TABLE IF EXISTS ONLY public.tipo_ausencia DROP CONSTRAINT IF EXISTS tipo_ausencia_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.rol_menu DROP CONSTRAINT IF EXISTS rol_menu_rol_id_fkey;
ALTER TABLE IF EXISTS ONLY public.rol_menu DROP CONSTRAINT IF EXISTS rol_menu_menu_id_fkey;
ALTER TABLE IF EXISTS ONLY public.regla_empresa DROP CONSTRAINT IF EXISTS regla_empresa_regla_id_fkey;
ALTER TABLE IF EXISTS ONLY public.regla_empresa DROP CONSTRAINT IF EXISTS regla_empresa_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.feriado DROP CONSTRAINT IF EXISTS feriado_region_id_fkey;
ALTER TABLE IF EXISTS ONLY public.empresa_servicio DROP CONSTRAINT IF EXISTS empresa_servicio_servicio_id_fkey;
ALTER TABLE IF EXISTS ONLY public.empresa_servicio DROP CONSTRAINT IF EXISTS empresa_servicio_empresa_id_fkey;
ALTER TABLE IF EXISTS ONLY public.empresa DROP CONSTRAINT IF EXISTS empresa_comuna_id_fkey;
ALTER TABLE IF EXISTS ONLY public.empresa DROP CONSTRAINT IF EXISTS empresa_cliente_id_fkey;
ALTER TABLE IF EXISTS ONLY public.comuna DROP CONSTRAINT IF EXISTS comuna_region_id_fkey;
DROP INDEX IF EXISTS public.ix_regla_empresa_empresa_id;
DROP INDEX IF EXISTS public.ix_regla_empresa_activo;
DROP INDEX IF EXISTS public.ix_regla_activo;
DROP INDEX IF EXISTS public.ix_region_codigo;
DROP INDEX IF EXISTS public.ix_region_activo;
DROP INDEX IF EXISTS public.ix_comuna_region_id;
DROP INDEX IF EXISTS public.ix_comuna_activo;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_rut_key;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_pkey;
ALTER TABLE IF EXISTS ONLY public.usuario_empresa DROP CONSTRAINT IF EXISTS usuario_empresa_pkey;
ALTER TABLE IF EXISTS ONLY public.usuario DROP CONSTRAINT IF EXISTS usuario_email_key;
ALTER TABLE IF EXISTS ONLY public.turno_plantilla DROP CONSTRAINT IF EXISTS turno_plantilla_pkey;
ALTER TABLE IF EXISTS ONLY public.turno_plantilla DROP CONSTRAINT IF EXISTS turno_plantilla_abreviacion_key;
ALTER TABLE IF EXISTS ONLY public.turno DROP CONSTRAINT IF EXISTS turno_pkey;
ALTER TABLE IF EXISTS ONLY public.trabajador DROP CONSTRAINT IF EXISTS trabajador_rut_key;
ALTER TABLE IF EXISTS ONLY public.trabajador_restriccion_turno DROP CONSTRAINT IF EXISTS trabajador_restriccion_turno_pkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_preferencia DROP CONSTRAINT IF EXISTS trabajador_preferencia_pkey;
ALTER TABLE IF EXISTS ONLY public.trabajador DROP CONSTRAINT IF EXISTS trabajador_pkey;
ALTER TABLE IF EXISTS ONLY public.trabajador_ausencia DROP CONSTRAINT IF EXISTS trabajador_ausencia_pkey;
ALTER TABLE IF EXISTS ONLY public.tipo_ausencia_plantilla DROP CONSTRAINT IF EXISTS tipo_ausencia_plantilla_pkey;
ALTER TABLE IF EXISTS ONLY public.tipo_ausencia_plantilla DROP CONSTRAINT IF EXISTS tipo_ausencia_plantilla_abreviacion_key;
ALTER TABLE IF EXISTS ONLY public.tipo_ausencia DROP CONSTRAINT IF EXISTS tipo_ausencia_pkey;
ALTER TABLE IF EXISTS ONLY public.servicio DROP CONSTRAINT IF EXISTS servicio_pkey;
ALTER TABLE IF EXISTS ONLY public.servicio DROP CONSTRAINT IF EXISTS servicio_descripcion_key;
ALTER TABLE IF EXISTS ONLY public.rol DROP CONSTRAINT IF EXISTS rol_pkey;
ALTER TABLE IF EXISTS ONLY public.rol_menu DROP CONSTRAINT IF EXISTS rol_menu_pkey;
ALTER TABLE IF EXISTS ONLY public.rol DROP CONSTRAINT IF EXISTS rol_descripcion_key;
ALTER TABLE IF EXISTS ONLY public.regla DROP CONSTRAINT IF EXISTS regla_pkey;
ALTER TABLE IF EXISTS ONLY public.regla_empresa DROP CONSTRAINT IF EXISTS regla_empresa_pkey;
ALTER TABLE IF EXISTS ONLY public.regla DROP CONSTRAINT IF EXISTS regla_codigo_key;
ALTER TABLE IF EXISTS ONLY public.region DROP CONSTRAINT IF EXISTS region_pkey;
ALTER TABLE IF EXISTS ONLY public.region DROP CONSTRAINT IF EXISTS region_codigo_key;
ALTER TABLE IF EXISTS ONLY public.parametro_legal DROP CONSTRAINT IF EXISTS parametro_legal_pkey;
ALTER TABLE IF EXISTS ONLY public.parametro_legal DROP CONSTRAINT IF EXISTS parametro_legal_codigo_key;
ALTER TABLE IF EXISTS ONLY public.menu DROP CONSTRAINT IF EXISTS menu_pkey;
ALTER TABLE IF EXISTS ONLY public.menu DROP CONSTRAINT IF EXISTS menu_nombre_key;
ALTER TABLE IF EXISTS ONLY public.feriado DROP CONSTRAINT IF EXISTS feriado_pkey;
ALTER TABLE IF EXISTS ONLY public.empresa_servicio DROP CONSTRAINT IF EXISTS empresa_servicio_pkey;
ALTER TABLE IF EXISTS ONLY public.empresa DROP CONSTRAINT IF EXISTS empresa_pkey;
ALTER TABLE IF EXISTS ONLY public.comuna DROP CONSTRAINT IF EXISTS comuna_pkey;
ALTER TABLE IF EXISTS ONLY public.comuna DROP CONSTRAINT IF EXISTS comuna_codigo_key;
ALTER TABLE IF EXISTS ONLY public.cliente DROP CONSTRAINT IF EXISTS cliente_rut_key;
ALTER TABLE IF EXISTS ONLY public.cliente DROP CONSTRAINT IF EXISTS cliente_pkey;
ALTER TABLE IF EXISTS ONLY public.cliente DROP CONSTRAINT IF EXISTS cliente_email_key;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.usuario_empresa ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.usuario ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.turno_plantilla ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.turno ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trabajador_restriccion_turno ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trabajador_preferencia ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trabajador_ausencia ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trabajador ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tipo_ausencia_plantilla ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tipo_ausencia ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.servicio ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.rol ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.regla_empresa ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.regla ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.region ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.parametro_legal ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.menu ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.feriado ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.empresa ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.comuna ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.cliente ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.usuario_id_seq;
DROP SEQUENCE IF EXISTS public.usuario_empresa_id_seq;
DROP TABLE IF EXISTS public.usuario_empresa;
DROP TABLE IF EXISTS public.usuario;
DROP SEQUENCE IF EXISTS public.turno_plantilla_id_seq;
DROP TABLE IF EXISTS public.turno_plantilla;
DROP SEQUENCE IF EXISTS public.turno_id_seq;
DROP TABLE IF EXISTS public.turno;
DROP SEQUENCE IF EXISTS public.trabajador_restriccion_turno_id_seq;
DROP TABLE IF EXISTS public.trabajador_restriccion_turno;
DROP SEQUENCE IF EXISTS public.trabajador_preferencia_id_seq;
DROP TABLE IF EXISTS public.trabajador_preferencia;
DROP SEQUENCE IF EXISTS public.trabajador_id_seq;
DROP SEQUENCE IF EXISTS public.trabajador_ausencia_id_seq;
DROP TABLE IF EXISTS public.trabajador_ausencia;
DROP TABLE IF EXISTS public.trabajador;
DROP SEQUENCE IF EXISTS public.tipo_ausencia_plantilla_id_seq;
DROP TABLE IF EXISTS public.tipo_ausencia_plantilla;
DROP SEQUENCE IF EXISTS public.tipo_ausencia_id_seq;
DROP TABLE IF EXISTS public.tipo_ausencia;
DROP SEQUENCE IF EXISTS public.servicio_id_seq;
DROP TABLE IF EXISTS public.servicio;
DROP TABLE IF EXISTS public.rol_menu;
DROP SEQUENCE IF EXISTS public.rol_id_seq;
DROP TABLE IF EXISTS public.rol;
DROP SEQUENCE IF EXISTS public.regla_id_seq;
DROP SEQUENCE IF EXISTS public.regla_empresa_id_seq;
DROP TABLE IF EXISTS public.regla_empresa;
DROP TABLE IF EXISTS public.regla;
DROP SEQUENCE IF EXISTS public.region_id_seq;
DROP TABLE IF EXISTS public.region;
DROP SEQUENCE IF EXISTS public.parametro_legal_id_seq;
DROP TABLE IF EXISTS public.parametro_legal;
DROP SEQUENCE IF EXISTS public.menu_id_seq;
DROP TABLE IF EXISTS public.menu;
DROP SEQUENCE IF EXISTS public.feriado_id_seq;
DROP TABLE IF EXISTS public.feriado;
DROP TABLE IF EXISTS public.empresa_servicio;
DROP SEQUENCE IF EXISTS public.empresa_id_seq;
DROP TABLE IF EXISTS public.empresa;
DROP SEQUENCE IF EXISTS public.comuna_id_seq;
DROP TABLE IF EXISTS public.comuna;
DROP SEQUENCE IF EXISTS public.cliente_id_seq;
DROP TABLE IF EXISTS public.cliente;
DROP TABLE IF EXISTS public.alembic_version;
DROP TYPE IF EXISTS public.tipocontrato;
DROP TYPE IF EXISTS public.categoriaausencia;
--
-- Name: categoriaausencia; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.categoriaausencia AS ENUM (
    'AUSENCIA',
    'RESTRICCION'
);


--
-- Name: tipocontrato; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipocontrato AS ENUM (
    'FULL_TIME',
    'PART_TIME_30',
    'PART_TIME_20'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: cliente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cliente (
    id integer NOT NULL,
    rut character varying(15) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cliente_id_seq OWNED BY public.cliente.id;


--
-- Name: comuna; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comuna (
    id integer NOT NULL,
    codigo character varying(20) NOT NULL,
    descripcion character varying(150) NOT NULL,
    region_id integer NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: comuna_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.comuna_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: comuna_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.comuna_id_seq OWNED BY public.comuna.id;


--
-- Name: empresa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empresa (
    id integer NOT NULL,
    rut character varying(15) NOT NULL,
    razon_social character varying(200) NOT NULL,
    cliente_id integer NOT NULL,
    comuna_id integer NOT NULL,
    direccion character varying(255) NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: empresa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.empresa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: empresa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.empresa_id_seq OWNED BY public.empresa.id;


--
-- Name: empresa_servicio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empresa_servicio (
    empresa_id integer NOT NULL,
    servicio_id integer NOT NULL
);


--
-- Name: feriado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feriado (
    id integer NOT NULL,
    fecha date NOT NULL,
    descripcion character varying(200) NOT NULL,
    es_regional boolean,
    region_id integer,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: feriado_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feriado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feriado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feriado_id_seq OWNED BY public.feriado.id;


--
-- Name: menu; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.menu (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(255),
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    endpoint character varying(100),
    icono character varying(50),
    orden integer DEFAULT 0 NOT NULL,
    es_base boolean DEFAULT false NOT NULL
);


--
-- Name: menu_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.menu_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: menu_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.menu_id_seq OWNED BY public.menu.id;


--
-- Name: parametro_legal; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parametro_legal (
    id integer NOT NULL,
    codigo character varying(60) NOT NULL,
    valor double precision NOT NULL,
    descripcion character varying(255),
    es_activo boolean NOT NULL,
    es_obligatorio boolean NOT NULL,
    actualizado_en timestamp without time zone,
    categoria character varying(50) DEFAULT 'General'::character varying NOT NULL
);


--
-- Name: parametro_legal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parametro_legal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parametro_legal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parametro_legal_id_seq OWNED BY public.parametro_legal.id;


--
-- Name: region; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.region (
    id integer NOT NULL,
    codigo character varying(10) NOT NULL,
    descripcion character varying(150) NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: region_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.region_id_seq OWNED BY public.region.id;


--
-- Name: regla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regla (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    familia character varying(50) NOT NULL,
    tipo_regla character varying(20) NOT NULL,
    scope character varying(50) NOT NULL,
    campo character varying(100),
    operador character varying(20),
    params_base json,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: regla_empresa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regla_empresa (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    regla_id integer NOT NULL,
    params_custom json,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    es_base boolean DEFAULT false NOT NULL
);


--
-- Name: regla_empresa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regla_empresa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regla_empresa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regla_empresa_id_seq OWNED BY public.regla_empresa.id;


--
-- Name: regla_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regla_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regla_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regla_id_seq OWNED BY public.regla.id;


--
-- Name: rol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol (
    id integer NOT NULL,
    descripcion character varying(100) NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: rol_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rol_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rol_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rol_id_seq OWNED BY public.rol.id;


--
-- Name: rol_menu; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol_menu (
    rol_id integer NOT NULL,
    menu_id integer NOT NULL,
    puede_crear boolean,
    puede_editar boolean,
    puede_eliminar boolean
);


--
-- Name: servicio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.servicio (
    id integer NOT NULL,
    descripcion character varying(100) NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone
);


--
-- Name: servicio_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.servicio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: servicio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.servicio_id_seq OWNED BY public.servicio.id;


--
-- Name: tipo_ausencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_ausencia (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    abreviacion character varying(5) NOT NULL,
    color character varying(10),
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    categoria public.categoriaausencia NOT NULL,
    tipo_restriccion character varying(30),
    es_base boolean DEFAULT false NOT NULL
);


--
-- Name: tipo_ausencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_ausencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_ausencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_ausencia_id_seq OWNED BY public.tipo_ausencia.id;


--
-- Name: tipo_ausencia_plantilla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_ausencia_plantilla (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    abreviacion character varying(5) NOT NULL,
    color character varying(10) DEFAULT '#95a5a6'::character varying,
    activo boolean DEFAULT true,
    creado_en timestamp without time zone DEFAULT now()
);


--
-- Name: tipo_ausencia_plantilla_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_ausencia_plantilla_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_ausencia_plantilla_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_ausencia_plantilla_id_seq OWNED BY public.tipo_ausencia_plantilla.id;


--
-- Name: trabajador; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trabajador (
    id integer NOT NULL,
    rut character varying(15) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido1 character varying(100) NOT NULL,
    apellido2 character varying(100),
    empresa_id integer NOT NULL,
    servicio_id integer NOT NULL,
    cargo character varying(100),
    email character varying(150),
    telefono character varying(20),
    tipo_contrato public.tipocontrato NOT NULL,
    horas_semanales integer DEFAULT 42 NOT NULL,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    permite_horas_extra boolean DEFAULT false
);


--
-- Name: trabajador_ausencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trabajador_ausencia (
    id integer NOT NULL,
    trabajador_id integer NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    motivo character varying(255) NOT NULL,
    tipo_ausencia_id integer,
    creado_en timestamp without time zone,
    restriccion_id integer
);


--
-- Name: trabajador_ausencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trabajador_ausencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trabajador_ausencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trabajador_ausencia_id_seq OWNED BY public.trabajador_ausencia.id;


--
-- Name: trabajador_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trabajador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trabajador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trabajador_id_seq OWNED BY public.trabajador.id;


--
-- Name: trabajador_preferencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trabajador_preferencia (
    id integer NOT NULL,
    trabajador_id integer NOT NULL,
    dia_semana integer NOT NULL,
    turno character varying(5) NOT NULL,
    tipo character varying(20) DEFAULT 'preferencia'::character varying NOT NULL
);


--
-- Name: trabajador_preferencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trabajador_preferencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trabajador_preferencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trabajador_preferencia_id_seq OWNED BY public.trabajador_preferencia.id;


--
-- Name: trabajador_restriccion_turno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trabajador_restriccion_turno (
    id integer NOT NULL,
    trabajador_id integer NOT NULL,
    empresa_id integer NOT NULL,
    tipo character varying(30) NOT NULL,
    naturaleza character varying(10) NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    dias_semana json,
    turno_id integer,
    turno_alternativo_id integer,
    motivo character varying(200),
    activo boolean,
    creado_en timestamp without time zone
);


--
-- Name: trabajador_restriccion_turno_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trabajador_restriccion_turno_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trabajador_restriccion_turno_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trabajador_restriccion_turno_id_seq OWNED BY public.trabajador_restriccion_turno.id;


--
-- Name: turno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.turno (
    id integer NOT NULL,
    empresa_id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    abreviacion character varying(5) NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fin time without time zone NOT NULL,
    color character varying(10),
    dotacion_diaria integer,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    es_nocturno boolean DEFAULT false NOT NULL,
    es_base boolean DEFAULT false NOT NULL
);


--
-- Name: turno_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.turno_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: turno_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.turno_id_seq OWNED BY public.turno.id;


--
-- Name: turno_plantilla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.turno_plantilla (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    abreviacion character varying(5) NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fin time without time zone NOT NULL,
    color character varying(10) DEFAULT '#18bc9c'::character varying,
    dotacion_diaria integer DEFAULT 1,
    es_nocturno boolean DEFAULT false,
    activo boolean DEFAULT true,
    creado_en timestamp without time zone DEFAULT now()
);


--
-- Name: turno_plantilla_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.turno_plantilla_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: turno_plantilla_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.turno_plantilla_id_seq OWNED BY public.turno_plantilla.id;


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario (
    id integer NOT NULL,
    rut character varying(15) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol_id integer NOT NULL,
    cliente_id integer,
    activo boolean,
    creado_en timestamp without time zone,
    actualizado_en timestamp without time zone,
    empresa_activa_id integer
);


--
-- Name: usuario_empresa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_empresa (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    empresa_id integer NOT NULL,
    activo boolean DEFAULT true,
    creado_en timestamp without time zone DEFAULT now()
);


--
-- Name: usuario_empresa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuario_empresa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuario_empresa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuario_empresa_id_seq OWNED BY public.usuario_empresa.id;


--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuario_id_seq OWNED BY public.usuario.id;


--
-- Name: cliente id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente ALTER COLUMN id SET DEFAULT nextval('public.cliente_id_seq'::regclass);


--
-- Name: comuna id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comuna ALTER COLUMN id SET DEFAULT nextval('public.comuna_id_seq'::regclass);


--
-- Name: empresa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa ALTER COLUMN id SET DEFAULT nextval('public.empresa_id_seq'::regclass);


--
-- Name: feriado id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feriado ALTER COLUMN id SET DEFAULT nextval('public.feriado_id_seq'::regclass);


--
-- Name: menu id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu ALTER COLUMN id SET DEFAULT nextval('public.menu_id_seq'::regclass);


--
-- Name: parametro_legal id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parametro_legal ALTER COLUMN id SET DEFAULT nextval('public.parametro_legal_id_seq'::regclass);


--
-- Name: region id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region ALTER COLUMN id SET DEFAULT nextval('public.region_id_seq'::regclass);


--
-- Name: regla id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla ALTER COLUMN id SET DEFAULT nextval('public.regla_id_seq'::regclass);


--
-- Name: regla_empresa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla_empresa ALTER COLUMN id SET DEFAULT nextval('public.regla_empresa_id_seq'::regclass);


--
-- Name: rol id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol ALTER COLUMN id SET DEFAULT nextval('public.rol_id_seq'::regclass);


--
-- Name: servicio id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicio ALTER COLUMN id SET DEFAULT nextval('public.servicio_id_seq'::regclass);


--
-- Name: tipo_ausencia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia ALTER COLUMN id SET DEFAULT nextval('public.tipo_ausencia_id_seq'::regclass);


--
-- Name: tipo_ausencia_plantilla id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia_plantilla ALTER COLUMN id SET DEFAULT nextval('public.tipo_ausencia_plantilla_id_seq'::regclass);


--
-- Name: trabajador id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador ALTER COLUMN id SET DEFAULT nextval('public.trabajador_id_seq'::regclass);


--
-- Name: trabajador_ausencia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_ausencia ALTER COLUMN id SET DEFAULT nextval('public.trabajador_ausencia_id_seq'::regclass);


--
-- Name: trabajador_preferencia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_preferencia ALTER COLUMN id SET DEFAULT nextval('public.trabajador_preferencia_id_seq'::regclass);


--
-- Name: trabajador_restriccion_turno id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno ALTER COLUMN id SET DEFAULT nextval('public.trabajador_restriccion_turno_id_seq'::regclass);


--
-- Name: turno id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno ALTER COLUMN id SET DEFAULT nextval('public.turno_id_seq'::regclass);


--
-- Name: turno_plantilla id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno_plantilla ALTER COLUMN id SET DEFAULT nextval('public.turno_plantilla_id_seq'::regclass);


--
-- Name: usuario id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id SET DEFAULT nextval('public.usuario_id_seq'::regclass);


--
-- Name: usuario_empresa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa ALTER COLUMN id SET DEFAULT nextval('public.usuario_empresa_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
aaab6f30d160
\.


--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cliente (id, rut, nombre, apellidos, email, activo, creado_en, actualizado_en) FROM stdin;
1	11111111-1	Admin	SGT	contacto@sgt.cl	t	2026-04-23 14:00:03.598242	2026-04-23 14:00:03.598244
2	157742477	Orlando	Ibañez	orozas@live.cl	t	2026-04-28 15:33:54.70719	2026-04-28 15:33:54.707195
\.


--
-- Data for Name: comuna; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.comuna (id, codigo, descripcion, region_id, activo, creado_en, actualizado_en) FROM stdin;
1	STGO	Santiago	1	t	2026-04-23 14:00:03.587558	2026-04-23 14:00:03.58756
\.


--
-- Data for Name: empresa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empresa (id, rut, razon_social, cliente_id, comuna_id, direccion, activo, creado_en, actualizado_en) FROM stdin;
1	76111111-1	Empresa Demo SGT	1	1	Av. Principal 123	t	2026-04-23 14:00:03.602016	2026-04-23 14:00:03.602018
2	15774247-6	EMPRESA DE ORLANDO SA	2	1	ALAMEDA	t	2026-04-28 15:34:30.761647	2026-04-28 15:34:30.761653
4	17823114-9	EMPRESA 2 ORLA	2	1	fgdfgdfgdf	t	2026-04-28 17:28:57.355921	2026-04-28 17:28:57.355926
\.


--
-- Data for Name: empresa_servicio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empresa_servicio (empresa_id, servicio_id) FROM stdin;
1	1
1	2
2	1
2	2
4	1
4	2
\.


--
-- Data for Name: feriado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feriado (id, fecha, descripcion, es_regional, region_id, activo, creado_en, actualizado_en) FROM stdin;
1	2025-01-01	Año Nuevo	f	\N	t	2026-04-23 14:00:03.591189	2026-04-23 14:00:03.591193
\.


--
-- Data for Name: menu; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.menu (id, nombre, descripcion, activo, creado_en, actualizado_en, endpoint, icono, orden, es_base) FROM stdin;
7	Empresas	\N	t	2026-04-23 14:00:03.596115	2026-04-28 15:10:00.22633	empresa.index	fa fa-building	21	f
5	Clientes	\N	t	2026-04-23 14:00:03.59611	2026-04-28 15:21:10.427706	cliente.index	fa fa-handshake	20	f
12	Servicios	\N	t	2026-04-28 15:21:10.428953	2026-04-28 15:21:10.428955	servicio.index	fa fa-concierge-bell	22	f
6	Usuarios	\N	t	2026-04-23 14:00:03.596113	2026-04-28 15:21:10.429762	usuario.index	fa fa-users-cog	23	f
13	Roles	\N	t	2026-04-28 15:21:10.430529	2026-04-28 15:21:10.430531	rol.index	fa fa-id-badge	24	f
15	Regiones	\N	t	2026-04-28 15:21:10.43189	2026-04-28 15:21:10.431892	region.index	fa fa-map-marked-alt	30	f
16	Comunas	\N	t	2026-04-28 15:21:10.432524	2026-04-28 15:21:10.432526	comuna.index	fa fa-map-pin	31	f
17	Feriados	\N	t	2026-04-28 15:21:10.433134	2026-04-28 15:21:10.433136	feriado.index	fa fa-umbrella-beach	32	f
18	Reglas Empresa	\N	t	2026-04-28 15:21:10.433833	2026-04-28 15:21:10.433836	regla_empresa.index	fa fa-briefcase	40	f
19	Reglas Familia	\N	t	2026-04-28 15:21:10.434418	2026-04-28 15:21:10.434421	main.reglas_familias	fa fa-layer-group	41	f
20	Reglas Generales	\N	t	2026-04-28 15:21:10.435013	2026-04-28 15:21:10.435016	regla.index	fa fa-cogs	42	f
22	Parámetros Legales	\N	t	2026-04-28 15:21:10.436345	2026-04-28 15:21:10.436347	parametro_legal.index	fa fa-gavel	44	f
1	Dashboard	\N	t	2026-04-23 14:00:03.5961	2026-04-28 15:26:44.933191	main.index	fa fa-th-large	1	t
2	Trabajadores	\N	t	2026-04-23 14:00:03.596104	2026-04-28 15:26:44.934491	trabajador.index	fa fa-users	2	t
3	Turnos	\N	t	2026-04-23 14:00:03.596106	2026-04-28 15:26:44.935482	turno.index	fa fa-clock	3	t
8	Ausencias	\N	t	2026-04-28 15:10:00.22234	2026-04-28 15:26:44.936273	ausencia.index	fa fa-calendar-times	4	t
11	Tipos de Ausencia	\N	t	2026-04-28 15:21:10.424094	2026-04-28 15:26:44.93716	tipo_ausencia.index	fa fa-user-minus	5	t
23	Planificacion	\N	t	2026-04-28 15:40:19.49293	2026-04-28 15:40:19.492933	main.planificacion	fa fa-calendar-alt	6	t
24	Simulacion	\N	t	2026-04-28 15:40:19.494363	2026-04-28 15:40:19.494366	main.simulacion	fa fa-robot	7	t
25	Menus	\N	t	2026-04-28 15:40:19.497522	2026-04-28 15:40:19.497525	menu.index	fa fa-list	25	f
26	Configuracion Reglas	\N	t	2026-04-28 15:40:19.501548	2026-04-28 15:40:19.501551	main.reglas_config	fa fa-sliders-h	43	f
27	Parametros Legales	\N	t	2026-04-28 15:49:05.257968	2026-04-28 15:49:05.257972	parametro_legal.index	fa fa-gavel	44	f
\.


--
-- Data for Name: parametro_legal; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.parametro_legal (id, codigo, valor, descripcion, es_activo, es_obligatorio, actualizado_en, categoria) FROM stdin;
1	MAX_HRS_SEMANA_FULL	42	Horas semanales maximas full-time (Ley 21.561)	t	t	2026-04-28 15:40:19.530706	Jornada
2	MAX_HRS_DIA_FULL	10	Jornada diaria maxima full-time (Art. 28 CT)	t	t	2026-04-28 15:40:19.53142	Jornada
3	MIN_DIAS_SEMANA_FULL	5	Dias minimos distribucion semanal full-time (Art. 28 CT)	t	t	2026-04-28 15:40:19.532103	Jornada
4	MAX_DIAS_SEMANA_FULL	6	Dias maximos distribucion semanal full-time (Art. 28 CT)	t	t	2026-04-28 15:40:19.532832	Jornada
5	MAX_HRS_SEMANA_PART_TIME_30	30	Jornada parcial maxima 30h (Art. 40 bis CT)	t	t	2026-04-28 15:40:19.533529	Jornada Parcial
6	MAX_HRS_SEMANA_PART_TIME_20	20	Jornada reducida maxima 20h	t	t	2026-04-28 15:40:19.53426	Jornada Parcial
7	MAX_HRS_DIA_PART_TIME	10	Jornada diaria maxima part-time (Art. 40 bis CT)	t	t	2026-04-28 15:40:19.534955	Jornada Parcial
8	MAX_DIAS_SEMANA_PART	5	Dias maximos distribucion semanal part-time	t	t	2026-04-28 15:40:19.535605	Jornada Parcial
9	UMBRAL_DIAS_DOMINGO_OBLIGATORIO	5	Dias/sem minimos para que aplique compensacion dominical	t	t	2026-04-28 15:40:19.536158	Descansos
10	MIN_DOMINGOS_LIBRES_MES	2	Domingos libres minimos/mes cuando aplica	t	t	2026-04-28 15:40:19.536872	Descansos
11	MAX_DIAS_CONSECUTIVOS	6	Dias consecutivos maximos de trabajo (Art. 38 CT)	t	t	2026-04-28 15:40:19.537614	Descansos
12	MIN_DESCANSO_ENTRE_TURNOS_HRS	12	Horas minimas de descanso entre dos turnos	t	t	2026-04-28 15:40:19.538213	Descansos
13	SEMANA_CORTA_UMBRAL_DIAS	5	Dias minimos para considerar semana completa	t	t	2026-04-28 15:40:19.538899	Semanas Cortas
14	SEMANA_CORTA_PRORRATEO	1	1 = prorratear horas proporcionales en semana corta	t	t	2026-04-28 15:40:19.539663	Semanas Cortas
15	W_CAMBIO_TURNO	150	Penalizacion por cambio de turno entre dias	t	f	2026-04-28 15:40:19.540581	Optimizacion
16	W_TURNO_DOMINANTE	80	Bonus por mantener un turno dominante	t	f	2026-04-28 15:40:19.544486	Optimizacion
17	W_NO_PREFERENTE	500	Penalizacion por no asignar turno preferente	t	f	2026-04-28 15:40:19.545037	Optimizacion
\.


--
-- Data for Name: region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region (id, codigo, descripcion, activo, creado_en, actualizado_en) FROM stdin;
1	RM	Región Metropolitana	t	2026-04-23 14:00:03.582415	2026-04-23 14:00:03.582419
\.


--
-- Data for Name: regla; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.regla (id, codigo, nombre, familia, tipo_regla, scope, campo, operador, params_base, activo, creado_en, actualizado_en) FROM stdin;
1	dias_descanso_post_6	Días de descanso tras 6 días trabajados	descanso	hard	empresa	dias_descanso	gte	{"value": 1}	t	2026-04-23 15:08:58.467858	2026-04-23 15:08:58.467858
2	jornada_semanal	Jornada semanal por defecto (horas)	contrato	hard	empresa	horas_semanales	eq	{"value": 42}	t	2026-04-23 15:08:58.467858	2026-04-23 15:08:58.467858
3	duracion_turno	Duración estándar del turno (horas)	contrato	hard	empresa	duracion_turno	eq	{"value": 8}	t	2026-04-23 15:08:58.467858	2026-04-23 15:08:58.467858
4	max_dias_consecutivos	Maximo dias consecutivos de trabajo	comparison	hard	client	dias_consecutivos	<=	{"valor": 6, "fuente_parametro": "MAX_DIAS_CONSECUTIVOS"}	t	2026-04-28 15:40:19.549832	2026-04-28 15:40:19.549835
5	no_doble_turno	No doble turno el mismo dia	assignment_constraint	hard	client	turnos_per_dia	<=	{"max_turnos_dia": 1}	t	2026-04-28 15:40:19.551734	2026-04-28 15:40:19.551736
6	max_horas_semana	Limite horas semanales segun contrato	comparison	hard	worker	horas_semanales	<=	{"fuente_parametro": "MAX_HRS_SEMANA_FULL"}	t	2026-04-28 15:40:19.55251	2026-04-28 15:40:19.552512
7	min_descanso_semanal	Dia libre semanal obligatorio	comparison	hard	client	dias_libres_semana	>=	{"valor": 1, "fuente_parametro": "MIN_DESCANSO_SEMANAL_DIAS"}	t	2026-04-28 15:40:19.55318	2026-04-28 15:40:19.553182
8	min_domingos_mes	Domingos libres minimos al mes	calendar	hard	worker	domingos_libres	>=	{"fuente_parametro": "MIN_DOMINGOS_LIBRES_MES", "condicion": "aplica_domingo_obligatorio"}	t	2026-04-28 15:40:19.553937	2026-04-28 15:40:19.553939
9	respetar_ausencias	Respetar vacaciones, licencias y permisos	calendar	hard	worker	trabajador_ausencia	==	{"bloquear": true}	t	2026-04-28 15:40:19.554641	2026-04-28 15:40:19.554643
10	cobertura_minima_turno	Dotacion minima requerida	assignment_constraint	hard	client	cobertura	>=	{"fuente": "matriz_dotacion"}	t	2026-04-28 15:40:19.555273	2026-04-28 15:40:19.555275
11	post_noche_libre	Libre al dia siguiente de turno noche	post_noche	hard	worker	es_nocturno	\N	{"condicional": true}	t	2026-04-28 15:40:19.555915	2026-04-28 15:40:19.555917
12	prefer_bloque_continuo	Preferir bloques de trabajo continuos	sequence	soft	client	bloque_trabajo	\N	{"min_dias": 4, "max_dias": 6, "fuente_min": "PREF_MIN_DIAS_BLOQUE", "fuente_max": "PREF_MAX_DIAS_BLOQUE", "penalty_weight": 100}	t	2026-04-28 15:40:19.556556	2026-04-28 15:40:19.556559
13	penalizar_dia_aislado	Evitar dias de trabajo aislados	sequence	soft	client	dia_aislado	\N	{"penalty_weight": 100, "fuente_penalty": "SOFT_PENALTY_DIA_AISLADO"}	t	2026-04-28 15:40:19.55719	2026-04-28 15:40:19.557192
14	penalizar_descanso_aislado	Evitar descansos aislados	sequence	soft	client	descanso_aislado	\N	{"penalty_weight": 80, "fuente_penalty": "SOFT_PENALTY_DESCANSO_AISLADO"}	t	2026-04-28 15:40:19.557827	2026-04-28 15:40:19.557829
15	balancear_noches	Equidad en turnos nocturnos	comparison	soft	client	turnos_noche	balance	{"penalty_weight": 10}	t	2026-04-28 15:40:19.558463	2026-04-28 15:40:19.558465
16	estabilidad_turno	Favorecer estabilidad de turno	sequence	soft	worker	cambio_turno	\N	{"penalty_cambio": 150, "bonus_dominante": 80, "fuente_penalty": "ESTAB_PENALTY_CAMBIO_TURNO"}	t	2026-04-28 15:40:19.559185	2026-04-28 15:40:19.559188
17	turno_preferente	Respetar turno preferente	worker_attribute	soft	worker	preferencia_turno	==	{"penalty_weight": 500, "fuente_penalty": "DEFAULT_PENALTY_NO_PREFERENTE"}	t	2026-04-28 15:40:19.559944	2026-04-28 15:40:19.559946
18	meta_mensual_horas	Cumplimiento de meta mensual de horas	comparison	soft	worker	total_horas_mes	range	{"penalty_weight": 50000}	t	2026-04-28 15:40:19.560551	2026-04-28 15:40:19.560553
\.


--
-- Data for Name: regla_empresa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.regla_empresa (id, empresa_id, regla_id, params_custom, activo, creado_en, actualizado_en, es_base) FROM stdin;
1	4	1	null	t	2026-04-28 17:28:57.374083	2026-04-28 17:28:57.374088	t
2	4	2	null	t	2026-04-28 17:28:57.374091	2026-04-28 17:28:57.374093	t
3	4	3	null	t	2026-04-28 17:28:57.374096	2026-04-28 17:28:57.374098	t
4	4	4	null	t	2026-04-28 17:28:57.3741	2026-04-28 17:28:57.374102	t
5	4	5	null	t	2026-04-28 17:28:57.374104	2026-04-28 17:28:57.374106	t
6	4	6	null	t	2026-04-28 17:28:57.374109	2026-04-28 17:28:57.37411	t
7	4	7	null	t	2026-04-28 17:28:57.374113	2026-04-28 17:28:57.374115	t
8	4	8	null	t	2026-04-28 17:28:57.374117	2026-04-28 17:28:57.374119	t
9	4	9	null	t	2026-04-28 17:28:57.374121	2026-04-28 17:28:57.374123	t
10	4	10	null	t	2026-04-28 17:28:57.374125	2026-04-28 17:28:57.374127	t
11	4	11	null	t	2026-04-28 17:28:57.374129	2026-04-28 17:28:57.374131	t
12	4	12	null	t	2026-04-28 17:28:57.374133	2026-04-28 17:28:57.374135	t
13	4	13	null	t	2026-04-28 17:28:57.374137	2026-04-28 17:28:57.374139	t
14	4	14	null	t	2026-04-28 17:28:57.374141	2026-04-28 17:28:57.374143	t
15	4	15	null	t	2026-04-28 17:28:57.374145	2026-04-28 17:28:57.374147	t
16	4	16	null	t	2026-04-28 17:28:57.374149	2026-04-28 17:28:57.374151	t
17	4	17	null	t	2026-04-28 17:28:57.374153	2026-04-28 17:28:57.374155	t
18	4	18	null	t	2026-04-28 17:28:57.374157	2026-04-28 17:28:57.374159	t
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rol (id, descripcion, activo, creado_en, actualizado_en) FROM stdin;
1	Super Admin	t	2026-04-23 14:00:03.593688	2026-04-23 14:00:03.59369
5	Cliente	t	2026-04-28 15:42:40.449677	2026-04-28 15:42:40.44968
6	Administrador	t	2026-04-28 15:42:40.450619	2026-04-28 15:42:40.450621
\.


--
-- Data for Name: rol_menu; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rol_menu (rol_id, menu_id, puede_crear, puede_editar, puede_eliminar) FROM stdin;
1	5	t	t	t
1	1	t	t	t
1	2	t	t	t
1	3	t	t	t
1	8	t	t	t
1	6	t	t	t
1	7	t	t	t
1	11	t	t	t
1	12	t	t	t
1	13	t	t	t
1	15	t	t	t
1	16	t	t	t
1	17	t	t	t
1	18	t	t	t
1	19	t	t	t
1	20	t	t	t
1	22	t	t	t
1	23	t	t	t
1	24	t	t	t
1	25	t	t	t
1	26	t	t	t
5	1	t	t	t
6	1	t	t	t
5	2	t	t	t
6	2	t	t	t
5	3	t	t	t
6	3	t	t	t
5	8	t	t	t
6	8	t	t	t
5	11	t	t	t
6	11	t	t	t
5	23	t	t	t
6	23	t	t	t
5	24	t	t	t
6	24	t	t	t
1	27	t	t	t
\.


--
-- Data for Name: servicio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.servicio (id, descripcion, activo, creado_en, actualizado_en) FROM stdin;
1	Pista Combustible	t	2026-04-23 14:00:03.604051	2026-04-23 14:00:03.604054
2	Tienda Pronto	t	2026-04-23 14:00:03.604055	2026-04-23 14:00:03.604056
\.


--
-- Data for Name: tipo_ausencia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_ausencia (id, empresa_id, nombre, abreviacion, color, activo, creado_en, actualizado_en, categoria, tipo_restriccion, es_base) FROM stdin;
2	1	Licencia medica	LM	#f01c05	t	2026-04-24 17:07:40.128377	2026-04-24 17:07:40.12838	AUSENCIA	\N	f
1	1	vacaciones	V	#7be740	t	2026-04-23 14:13:37.134408	2026-04-24 17:07:54.739666	AUSENCIA	\N	f
4	1	Permiso con goce	PCG	#f39c12	t	2026-04-27 21:55:04.976726	2026-04-27 21:55:04.976728	AUSENCIA	\N	f
5	1	Permiso sin goce	PSG	#95a5a6	t	2026-04-27 21:55:04.97748	2026-04-27 21:55:04.977481	AUSENCIA	\N	f
6	1	Día compensatorio	COMP	#9b59b6	t	2026-04-27 21:55:04.978165	2026-04-27 21:55:04.978167	AUSENCIA	\N	f
7	1	Turno fijo	TF	#27ae60	t	2026-04-27 21:55:04.978847	2026-04-27 21:55:04.978849	RESTRICCION	turno_fijo	f
8	1	Excluir turno	ET	#c0392b	t	2026-04-27 21:55:04.979505	2026-04-27 21:55:04.979507	RESTRICCION	excluir_turno	f
9	1	Solo turno	ST	#2980b9	t	2026-04-27 21:55:04.980223	2026-04-27 21:55:04.980226	RESTRICCION	solo_turno	f
10	1	Turno preferente	TP	#f1c40f	t	2026-04-27 21:55:04.980891	2026-04-27 21:55:04.980893	RESTRICCION	turno_preferente	f
11	1	Post noche libre	PNL	#1abc9c	t	2026-04-27 21:55:04.981423	2026-04-27 21:55:04.981425	RESTRICCION	post_noche	f
3	1	Vacaciones	VAC	#58db33	t	2026-04-27 21:55:04.974755	2026-04-28 02:04:22.522152	AUSENCIA	\N	f
12	2	Vacaciones	VAC	#3498db	t	2026-04-28 15:40:19.570797	2026-04-28 15:40:19.5708	AUSENCIA	\N	f
13	2	Licencia médica	LM	#e74c3c	t	2026-04-28 15:40:19.57178	2026-04-28 15:40:19.571782	AUSENCIA	\N	f
14	2	Permiso con goce	PCG	#f39c12	t	2026-04-28 15:40:19.572499	2026-04-28 15:40:19.5725	AUSENCIA	\N	f
15	2	Permiso sin goce	PSG	#95a5a6	t	2026-04-28 15:40:19.573223	2026-04-28 15:40:19.573225	AUSENCIA	\N	f
16	2	Día compensatorio	COMP	#9b59b6	t	2026-04-28 15:40:19.573898	2026-04-28 15:40:19.5739	AUSENCIA	\N	f
17	2	Turno fijo	TF	#27ae60	t	2026-04-28 15:40:19.574607	2026-04-28 15:40:19.574609	RESTRICCION	turno_fijo	f
18	2	Excluir turno	ET	#c0392b	t	2026-04-28 15:40:19.575365	2026-04-28 15:40:19.575367	RESTRICCION	excluir_turno	f
19	2	Solo turno	ST	#2980b9	t	2026-04-28 15:40:19.576028	2026-04-28 15:40:19.57603	RESTRICCION	solo_turno	f
20	2	Turno preferente	TP	#f1c40f	t	2026-04-28 15:40:19.576664	2026-04-28 15:40:19.576666	RESTRICCION	turno_preferente	f
21	2	Post noche libre	PNL	#1abc9c	t	2026-04-28 15:40:19.577227	2026-04-28 15:40:19.577229	RESTRICCION	post_noche	f
\.


--
-- Data for Name: tipo_ausencia_plantilla; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_ausencia_plantilla (id, nombre, abreviacion, color, activo, creado_en) FROM stdin;
\.


--
-- Data for Name: trabajador; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trabajador (id, rut, nombre, apellido1, apellido2, empresa_id, servicio_id, cargo, email, telefono, tipo_contrato, horas_semanales, activo, creado_en, actualizado_en, permite_horas_extra) FROM stdin;
2	10100002-2	Ana	Torres	None	1	1	Operario	ana@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.618778	2026-04-24 19:03:57.433829	t
1	10100001-1	Carlos	Muñoz	None	1	1	Operario	carlos@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.618774	2026-04-23 14:04:53.538637	t
3	10100003-3	Diego	Salinas	None	1	1	Cajero	diego@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.61878	2026-04-23 14:00:53.725874	t
4	10100004-4	Valentina	Reyes	None	1	1	Cajero	valentina@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.618783	2026-04-23 14:00:58.96753	t
5	10100005-5	Felipe	Contreras	None	1	1	Operario	felipe@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.618785	2026-04-23 19:55:56.807275	t
6	10100006-6	Claudia	Fernández	None	1	1	Cajera	claudia@sgt.cl	None	FULL_TIME	42	t	2026-04-23 14:00:03.618787	2026-04-23 14:00:48.656939	t
7	157742477	Orlando	Rozas	Rozas	1	1	sasdasd	orlandorozasi@gmail.com	0984530346	PART_TIME_30	20	t	2026-04-24 16:10:10.594545	2026-04-28 03:57:23.969333	t
8	11111111-1	Juan	Perez	\N	2	1	\N	j.perez@email.com	\N	FULL_TIME	42	t	2026-04-28 15:56:28.917738	2026-04-28 15:56:28.917741	f
9	22222222-2	Maria	Gonzalez	\N	2	1	\N	m.gonzalez@email.com	\N	FULL_TIME	42	t	2026-04-28 15:56:28.920111	2026-04-28 15:56:28.920113	f
11	44444444-4	Ana	Rojas	\N	2	1	\N	a.rojas@email.com	\N	FULL_TIME	42	t	2026-04-28 15:56:28.92175	2026-04-28 15:56:28.921752	f
12	55555555-5	Luis	Morales	\N	2	1	\N	l.morales@email.com	\N	FULL_TIME	42	t	2026-04-28 15:56:28.922422	2026-04-28 15:56:28.922423	f
10	33333333-3	Carlos	Soto	None	2	1	None	c.soto@email.com	None	PART_TIME_30	30	t	2026-04-28 15:56:28.920945	2026-04-28 17:12:13.437338	f
13	15774247-7	TEST DE TRABAJADOR	TEST		4	1	sadasdasd	423423@gsfs.com	3424324	PART_TIME_30	37	t	2026-04-28 17:31:54.480528	2026-04-28 17:31:54.480533	f
\.


--
-- Data for Name: trabajador_ausencia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trabajador_ausencia (id, trabajador_id, fecha_inicio, fecha_fin, motivo, tipo_ausencia_id, creado_en, restriccion_id) FROM stdin;
24	7	2026-05-25	2026-05-30	Turno Fijo Mañana	7	2026-04-28 03:46:37.346426	15
25	7	2026-05-31	2026-05-31		9	2026-04-28 03:47:23.755247	16
26	6	2026-04-27	2026-05-03		11	2026-04-28 12:38:35.090262	17
27	2	2026-04-28	2026-05-03	se quebro la pata	2	2026-04-28 14:48:10.714651	\N
28	11	2026-05-04	2026-05-10	vacas	1	2026-04-28 17:18:09.747963	\N
\.


--
-- Data for Name: trabajador_preferencia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trabajador_preferencia (id, trabajador_id, dia_semana, turno, tipo) FROM stdin;
120	2	0	N	solo_turno
121	2	1	N	solo_turno
122	2	2	N	solo_turno
123	2	3	N	solo_turno
124	2	4	N	solo_turno
125	2	5	N	solo_turno
126	2	6	N	solo_turno
127	13	0	M	fijo
\.


--
-- Data for Name: trabajador_restriccion_turno; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trabajador_restriccion_turno (id, trabajador_id, empresa_id, tipo, naturaleza, fecha_inicio, fecha_fin, dias_semana, turno_id, turno_alternativo_id, motivo, activo, creado_en) FROM stdin;
2	1	1	solo_turno	hard	2026-05-01	2026-05-31	[1]	1	\N	test	t	2026-04-27 21:58:55.440392
1	2	1	turno_fijo	hard	2026-05-01	2026-05-31	[0, 3]	1	\N	prueba turno fijo	t	2026-04-27 21:43:11.93144
15	7	1	turno_fijo	hard	2026-05-25	2026-05-30	[0, 3]	1	\N	Turno Fijo Mañana	t	2026-04-28 03:46:37.343583
16	7	1	solo_turno	hard	2026-05-31	2026-05-31	[6]	1	\N		t	2026-04-28 03:47:23.751884
17	6	1	post_noche	hard	2026-04-27	2026-05-03	[4]	1	\N		t	2026-04-28 12:38:35.082468
\.


--
-- Data for Name: turno; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.turno (id, empresa_id, nombre, abreviacion, hora_inicio, hora_fin, color, dotacion_diaria, activo, creado_en, actualizado_en, es_nocturno, es_base) FROM stdin;
1	1	MAÑANA	M	07:00:00	15:00:00	#3498db	2	t	2026-04-23 14:00:03.613762	2026-04-23 14:34:30.079648	f	f
3	1	NOCHE	N	23:00:00	07:00:00	#2c3e50	1	t	2026-04-23 14:00:03.613768	2026-04-23 14:35:12.231063	t	f
5	1	TEST	T1	16:58:00	17:59:00	#18bc9c	2	f	2026-04-27 20:58:43.048781	2026-04-28 03:16:36.786583	f	f
2	1	TARDE	T	15:00:00	23:00:00	#e67e22	1	t	2026-04-23 14:00:03.613766	2026-04-28 03:16:46.965607	f	f
4	1	INTERMEDIO	I	11:00:00	19:00:00	#1abc9c	1	t	2026-04-23 14:00:03.61377	2026-04-28 04:03:59.123809	f	f
9	2	Mañana	M	08:00:00	16:00:00	#f1c40f	1	t	2026-04-28 15:56:28.91191	2026-04-28 15:56:28.911913	f	f
11	2	Noche	N	00:00:00	08:00:00	#2c3e50	1	t	2026-04-28 15:56:28.91464	2026-04-28 15:56:28.914642	t	f
10	2	Tarde	T	16:00:00	23:00:00	#e67e22	1	t	2026-04-28 15:56:28.913821	2026-04-28 17:10:05.161958	f	f
12	2	NOCGHE	NC	22:00:00	07:00:00	#1f1d20	1	t	2026-04-28 17:10:58.316206	2026-04-28 17:10:58.316211	t	f
\.


--
-- Data for Name: turno_plantilla; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.turno_plantilla (id, nombre, abreviacion, hora_inicio, hora_fin, color, dotacion_diaria, es_nocturno, activo, creado_en) FROM stdin;
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario (id, rut, nombre, apellidos, email, password_hash, rol_id, cliente_id, activo, creado_en, actualizado_en, empresa_activa_id) FROM stdin;
1	99999999-9	Admin	Sistema	admin@sgt.cl	scrypt:32768:8:1$69L26B5JTpy3MDKJ$f9f8d344dccdbef8ddf45d66e1b60e998cb34bf860766b8e76d31abccd90dd0e41dd77d26cb243de738322672aa18bf52b8d0f19a0838f16cf64ffc2f6044247	1	\N	t	2026-04-23 14:00:03.622643	2026-04-28 17:04:02.542834	\N
2	157742477	Orlando	Usuario	orlando@sgt.cl	scrypt:32768:8:1$fADfubsDlluCqEOV$b796219e0b8a45129f43ae630db2abd55f55ab775d26f58871b61b18d7c4701f1f7e3f273ee83d8cc115daf84295f20d683a4f788059bf5b9504720de8acc0d4	5	2	t	2026-04-28 15:45:21.790188	2026-04-28 17:48:39.156803	4
\.


--
-- Data for Name: usuario_empresa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_empresa (id, usuario_id, empresa_id, activo, creado_en) FROM stdin;
1	1	1	t	2026-04-28 15:10:00.245036
2	2	1	t	2026-04-28 15:45:21.797725
3	2	2	t	2026-04-28 15:46:36.838456
\.


--
-- Name: cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cliente_id_seq', 2, true);


--
-- Name: comuna_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.comuna_id_seq', 1, true);


--
-- Name: empresa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empresa_id_seq', 4, true);


--
-- Name: feriado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.feriado_id_seq', 1, true);


--
-- Name: menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.menu_id_seq', 27, true);


--
-- Name: parametro_legal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.parametro_legal_id_seq', 17, true);


--
-- Name: region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_id_seq', 1, true);


--
-- Name: regla_empresa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.regla_empresa_id_seq', 18, true);


--
-- Name: regla_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.regla_id_seq', 18, true);


--
-- Name: rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_id_seq', 6, true);


--
-- Name: servicio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.servicio_id_seq', 2, true);


--
-- Name: tipo_ausencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_ausencia_id_seq', 21, true);


--
-- Name: tipo_ausencia_plantilla_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_ausencia_plantilla_id_seq', 1, false);


--
-- Name: trabajador_ausencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trabajador_ausencia_id_seq', 28, true);


--
-- Name: trabajador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trabajador_id_seq', 13, true);


--
-- Name: trabajador_preferencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trabajador_preferencia_id_seq', 127, true);


--
-- Name: trabajador_restriccion_turno_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trabajador_restriccion_turno_id_seq', 17, true);


--
-- Name: turno_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.turno_id_seq', 12, true);


--
-- Name: turno_plantilla_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.turno_plantilla_id_seq', 1, false);


--
-- Name: usuario_empresa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_empresa_id_seq', 3, true);


--
-- Name: usuario_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_id_seq', 2, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: cliente cliente_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_email_key UNIQUE (email);


--
-- Name: cliente cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_pkey PRIMARY KEY (id);


--
-- Name: cliente cliente_rut_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cliente
    ADD CONSTRAINT cliente_rut_key UNIQUE (rut);


--
-- Name: comuna comuna_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comuna
    ADD CONSTRAINT comuna_codigo_key UNIQUE (codigo);


--
-- Name: comuna comuna_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comuna
    ADD CONSTRAINT comuna_pkey PRIMARY KEY (id);


--
-- Name: empresa empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_pkey PRIMARY KEY (id);


--
-- Name: empresa_servicio empresa_servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa_servicio
    ADD CONSTRAINT empresa_servicio_pkey PRIMARY KEY (empresa_id, servicio_id);


--
-- Name: feriado feriado_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feriado
    ADD CONSTRAINT feriado_pkey PRIMARY KEY (id);


--
-- Name: menu menu_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu
    ADD CONSTRAINT menu_nombre_key UNIQUE (nombre);


--
-- Name: menu menu_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.menu
    ADD CONSTRAINT menu_pkey PRIMARY KEY (id);


--
-- Name: parametro_legal parametro_legal_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parametro_legal
    ADD CONSTRAINT parametro_legal_codigo_key UNIQUE (codigo);


--
-- Name: parametro_legal parametro_legal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parametro_legal
    ADD CONSTRAINT parametro_legal_pkey PRIMARY KEY (id);


--
-- Name: region region_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_codigo_key UNIQUE (codigo);


--
-- Name: region region_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pkey PRIMARY KEY (id);


--
-- Name: regla regla_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla
    ADD CONSTRAINT regla_codigo_key UNIQUE (codigo);


--
-- Name: regla_empresa regla_empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla_empresa
    ADD CONSTRAINT regla_empresa_pkey PRIMARY KEY (id);


--
-- Name: regla regla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla
    ADD CONSTRAINT regla_pkey PRIMARY KEY (id);


--
-- Name: rol rol_descripcion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_descripcion_key UNIQUE (descripcion);


--
-- Name: rol_menu rol_menu_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_menu
    ADD CONSTRAINT rol_menu_pkey PRIMARY KEY (rol_id, menu_id);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id);


--
-- Name: servicio servicio_descripcion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicio
    ADD CONSTRAINT servicio_descripcion_key UNIQUE (descripcion);


--
-- Name: servicio servicio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.servicio
    ADD CONSTRAINT servicio_pkey PRIMARY KEY (id);


--
-- Name: tipo_ausencia tipo_ausencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia
    ADD CONSTRAINT tipo_ausencia_pkey PRIMARY KEY (id);


--
-- Name: tipo_ausencia_plantilla tipo_ausencia_plantilla_abreviacion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia_plantilla
    ADD CONSTRAINT tipo_ausencia_plantilla_abreviacion_key UNIQUE (abreviacion);


--
-- Name: tipo_ausencia_plantilla tipo_ausencia_plantilla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia_plantilla
    ADD CONSTRAINT tipo_ausencia_plantilla_pkey PRIMARY KEY (id);


--
-- Name: trabajador_ausencia trabajador_ausencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_ausencia
    ADD CONSTRAINT trabajador_ausencia_pkey PRIMARY KEY (id);


--
-- Name: trabajador trabajador_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_pkey PRIMARY KEY (id);


--
-- Name: trabajador_preferencia trabajador_preferencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_preferencia
    ADD CONSTRAINT trabajador_preferencia_pkey PRIMARY KEY (id);


--
-- Name: trabajador_restriccion_turno trabajador_restriccion_turno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno
    ADD CONSTRAINT trabajador_restriccion_turno_pkey PRIMARY KEY (id);


--
-- Name: trabajador trabajador_rut_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_rut_key UNIQUE (rut);


--
-- Name: turno turno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno
    ADD CONSTRAINT turno_pkey PRIMARY KEY (id);


--
-- Name: turno_plantilla turno_plantilla_abreviacion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno_plantilla
    ADD CONSTRAINT turno_plantilla_abreviacion_key UNIQUE (abreviacion);


--
-- Name: turno_plantilla turno_plantilla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno_plantilla
    ADD CONSTRAINT turno_plantilla_pkey PRIMARY KEY (id);


--
-- Name: usuario usuario_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_email_key UNIQUE (email);


--
-- Name: usuario_empresa usuario_empresa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_pkey PRIMARY KEY (id);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- Name: usuario usuario_rut_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_rut_key UNIQUE (rut);


--
-- Name: ix_comuna_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_comuna_activo ON public.comuna USING btree (activo);


--
-- Name: ix_comuna_region_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_comuna_region_id ON public.comuna USING btree (region_id);


--
-- Name: ix_region_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_region_activo ON public.region USING btree (activo);


--
-- Name: ix_region_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_region_codigo ON public.region USING btree (codigo);


--
-- Name: ix_regla_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regla_activo ON public.regla USING btree (activo);


--
-- Name: ix_regla_empresa_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regla_empresa_activo ON public.regla_empresa USING btree (activo);


--
-- Name: ix_regla_empresa_empresa_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_regla_empresa_empresa_id ON public.regla_empresa USING btree (empresa_id);


--
-- Name: comuna comuna_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comuna
    ADD CONSTRAINT comuna_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.region(id) ON DELETE RESTRICT;


--
-- Name: empresa empresa_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id) ON DELETE RESTRICT;


--
-- Name: empresa empresa_comuna_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa
    ADD CONSTRAINT empresa_comuna_id_fkey FOREIGN KEY (comuna_id) REFERENCES public.comuna(id) ON DELETE RESTRICT;


--
-- Name: empresa_servicio empresa_servicio_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa_servicio
    ADD CONSTRAINT empresa_servicio_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: empresa_servicio empresa_servicio_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresa_servicio
    ADD CONSTRAINT empresa_servicio_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON DELETE CASCADE;


--
-- Name: feriado feriado_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feriado
    ADD CONSTRAINT feriado_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.region(id) ON DELETE CASCADE;


--
-- Name: regla_empresa regla_empresa_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla_empresa
    ADD CONSTRAINT regla_empresa_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: regla_empresa regla_empresa_regla_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regla_empresa
    ADD CONSTRAINT regla_empresa_regla_id_fkey FOREIGN KEY (regla_id) REFERENCES public.regla(id) ON DELETE CASCADE;


--
-- Name: rol_menu rol_menu_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_menu
    ADD CONSTRAINT rol_menu_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.menu(id) ON DELETE CASCADE;


--
-- Name: rol_menu rol_menu_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_menu
    ADD CONSTRAINT rol_menu_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id) ON DELETE CASCADE;


--
-- Name: tipo_ausencia tipo_ausencia_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ausencia
    ADD CONSTRAINT tipo_ausencia_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: trabajador_ausencia trabajador_ausencia_restriccion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_ausencia
    ADD CONSTRAINT trabajador_ausencia_restriccion_id_fkey FOREIGN KEY (restriccion_id) REFERENCES public.trabajador_restriccion_turno(id);


--
-- Name: trabajador_ausencia trabajador_ausencia_tipo_ausencia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_ausencia
    ADD CONSTRAINT trabajador_ausencia_tipo_ausencia_id_fkey FOREIGN KEY (tipo_ausencia_id) REFERENCES public.tipo_ausencia(id) ON DELETE CASCADE;


--
-- Name: trabajador_ausencia trabajador_ausencia_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_ausencia
    ADD CONSTRAINT trabajador_ausencia_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id) ON DELETE CASCADE;


--
-- Name: trabajador trabajador_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE RESTRICT;


--
-- Name: trabajador_preferencia trabajador_preferencia_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_preferencia
    ADD CONSTRAINT trabajador_preferencia_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id) ON DELETE CASCADE;


--
-- Name: trabajador_restriccion_turno trabajador_restriccion_turno_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno
    ADD CONSTRAINT trabajador_restriccion_turno_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: trabajador_restriccion_turno trabajador_restriccion_turno_trabajador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno
    ADD CONSTRAINT trabajador_restriccion_turno_trabajador_id_fkey FOREIGN KEY (trabajador_id) REFERENCES public.trabajador(id) ON DELETE CASCADE;


--
-- Name: trabajador_restriccion_turno trabajador_restriccion_turno_turno_alternativo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno
    ADD CONSTRAINT trabajador_restriccion_turno_turno_alternativo_id_fkey FOREIGN KEY (turno_alternativo_id) REFERENCES public.turno(id) ON DELETE RESTRICT;


--
-- Name: trabajador_restriccion_turno trabajador_restriccion_turno_turno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador_restriccion_turno
    ADD CONSTRAINT trabajador_restriccion_turno_turno_id_fkey FOREIGN KEY (turno_id) REFERENCES public.turno(id) ON DELETE RESTRICT;


--
-- Name: trabajador trabajador_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trabajador
    ADD CONSTRAINT trabajador_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicio(id) ON DELETE RESTRICT;


--
-- Name: turno turno_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turno
    ADD CONSTRAINT turno_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: usuario usuario_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.cliente(id) ON DELETE CASCADE;


--
-- Name: usuario usuario_empresa_activa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_empresa_activa_id_fkey FOREIGN KEY (empresa_activa_id) REFERENCES public.empresa(id) ON DELETE SET NULL;


--
-- Name: usuario_empresa usuario_empresa_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresa(id) ON DELETE CASCADE;


--
-- Name: usuario_empresa usuario_empresa_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_empresa
    ADD CONSTRAINT usuario_empresa_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id) ON DELETE CASCADE;


--
-- Name: usuario usuario_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.rol(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--


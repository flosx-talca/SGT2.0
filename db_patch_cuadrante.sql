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

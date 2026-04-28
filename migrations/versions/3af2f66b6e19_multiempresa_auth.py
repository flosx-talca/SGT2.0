"""multiempresa_auth

Revision ID: 3af2f66b6e19
Revises: c18184e4a3f7
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3af2f66b6e19'
down_revision = 'c18184e4a3f7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tabla usuario_empresa
    op.create_table(
        'usuario_empresa',
        sa.Column('id',         sa.Integer,  primary_key=True),
        sa.Column('usuario_id', sa.Integer,
                  sa.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False),
        sa.Column('empresa_id', sa.Integer,
                  sa.ForeignKey('empresa.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activo',     sa.Boolean,  server_default='true', nullable=False),
        sa.Column('creado_en',  sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('usuario_id', 'empresa_id', name='uq_usuario_empresa'),
    )
    op.create_index('ix_ue_usuario', 'usuario_empresa', ['usuario_id'])
    op.create_index('ix_ue_empresa', 'usuario_empresa', ['empresa_id'])

    # 2. empresa_activa_id en usuario
    op.add_column('usuario',
        sa.Column('empresa_activa_id', sa.Integer,
                  sa.ForeignKey('empresa.id', ondelete='SET NULL'), nullable=True))

    # 3. endpoint, icono, orden en menu
    op.add_column('menu', sa.Column('endpoint', sa.String(100), nullable=True))
    op.add_column('menu', sa.Column('icono',    sa.String(50),  nullable=True))
    op.add_column('menu', sa.Column('orden',    sa.Integer,
                                    server_default='0', nullable=False))

    # 4. es_base en turno, tipo_ausencia, regla_empresa
    for tabla in ['turno', 'tipo_ausencia', 'regla_empresa']:
        op.add_column(tabla,
            sa.Column('es_base', sa.Boolean,
                      server_default='false', nullable=False))

    # 5. Tabla turno_plantilla
    op.create_table(
        'turno_plantilla',
        sa.Column('id',              sa.Integer, primary_key=True),
        sa.Column('nombre',          sa.String(50),  nullable=False),
        sa.Column('abreviacion',     sa.String(5),   nullable=False, unique=True),
        sa.Column('hora_inicio',     sa.Time(timezone=False), nullable=False),
        sa.Column('hora_fin',        sa.Time(timezone=False), nullable=False),
        sa.Column('color',           sa.String(10),  server_default='#18bc9c'),
        sa.Column('dotacion_diaria', sa.Integer,     server_default='1'),
        sa.Column('es_nocturno',     sa.Boolean,     server_default='false'),
        sa.Column('activo',          sa.Boolean,     server_default='true'),
        sa.Column('creado_en',       sa.DateTime,    server_default=sa.func.now()),
    )

    # 6. Tabla tipo_ausencia_plantilla
    op.create_table(
        'tipo_ausencia_plantilla',
        sa.Column('id',          sa.Integer,    primary_key=True),
        sa.Column('nombre',      sa.String(50), nullable=False),
        sa.Column('abreviacion', sa.String(5),  nullable=False, unique=True),
        sa.Column('color',       sa.String(10), server_default='#95a5a6'),
        sa.Column('activo',      sa.Boolean,    server_default='true'),
        sa.Column('creado_en',   sa.DateTime,   server_default=sa.func.now()),
    )

    # 7. Quitar unique de empresa.rut (permite varias sucursales con mismo RUT)
    try:
        op.drop_constraint('empresa_rut_key', 'empresa', type_='unique')
    except Exception:
        pass


def downgrade():
    op.create_unique_constraint('empresa_rut_key', 'empresa', ['rut'])
    op.drop_table('tipo_ausencia_plantilla')
    op.drop_table('turno_plantilla')
    for tabla in ['turno', 'tipo_ausencia', 'regla_empresa']:
        op.drop_column(tabla, 'es_base')
    op.drop_column('menu', 'orden')
    op.drop_column('menu', 'icono')
    op.drop_column('menu', 'endpoint')
    op.drop_column('usuario', 'empresa_activa_id')
    op.drop_index('ix_ue_empresa', 'usuario_empresa')
    op.drop_index('ix_ue_usuario', 'usuario_empresa')
    op.drop_table('usuario_empresa')

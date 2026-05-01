"""add_regimen_exceptuado_to_empresa

Revision ID: a1b2c3d4e5f7
Revises: 24d78431b0e4
Create Date: 2026-04-30 23:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '24d78431b0e4'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campo regimen_exceptuado a la tabla empresa
    # Default True: la mayoría de las empresas en SGT son de régimen exceptuado (Art. 38 CT)
    with op.batch_alter_table('empresa', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'regimen_exceptuado',
            sa.Boolean(),
            server_default='true',
            nullable=False
        ))

    # Renombrar y actualizar el parámetro legal de umbral de domingos
    # UMBRAL_DIAS_DOMINGO_OBLIGATORIO (5.0 días) → UMBRAL_HRS_DOMINGO_OBLIGATORIO (20.0 horas)
    # Esto alinea el criterio con el Art. 38 inc. 4° CT (excepción para jornadas <= 20h/sem)
    op.execute("""
        UPDATE parametro_legal
        SET codigo       = 'UMBRAL_HRS_DOMINGO_OBLIGATORIO',
            valor        = 20.0,
            descripcion  = 'Jornada mínima (horas/semana) para que apliquen los 2 domingos libres obligatorios/mes. HR7 activa si horas_semanales > este_valor. Valor legal = 20 (Art. 38 inc. 4 CT). NO modificar sin visación legal.',
            categoria    = 'Descansos'
        WHERE codigo = 'UMBRAL_DIAS_DOMINGO_OBLIGATORIO'
    """)


def downgrade():
    with op.batch_alter_table('empresa', schema=None) as batch_op:
        batch_op.drop_column('regimen_exceptuado')

    op.execute("""
        UPDATE parametro_legal
        SET codigo       = 'UMBRAL_DIAS_DOMINGO_OBLIGATORIO',
            valor        = 5.0,
            descripcion  = 'Dias/sem minimos para que aplique compensacion dominical',
            categoria    = 'Descansos'
        WHERE codigo = 'UMBRAL_HRS_DOMINGO_OBLIGATORIO'
    """)

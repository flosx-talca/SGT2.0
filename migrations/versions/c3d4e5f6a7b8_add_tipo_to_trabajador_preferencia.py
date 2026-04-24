"""add tipo to trabajador_preferencia

Revision ID: c3d4e5f6a7b8
Revises: None
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna tipo con default 'preferencia'
    op.add_column(
        'trabajador_preferencia',
        sa.Column('tipo', sa.String(20), nullable=False,
                  server_default='preferencia')
    )

    # Todos los registros existentes quedan como 'preferencia'
    op.execute(text("""
        UPDATE trabajador_preferencia
        SET tipo = 'preferencia'
        WHERE tipo IS NULL
    """))

    print("✅ Campo tipo agregado a trabajador_preferencia")


def downgrade():
    op.drop_column('trabajador_preferencia', 'tipo')

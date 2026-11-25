"""Miniatura privada da referência facial. Revision 0029."""

import sqlalchemy as sa
from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "biometria", sa.Column("foto_perfil", sa.LargeBinary()), schema="academia"
    )


def downgrade() -> None:
    op.drop_column("biometria", "foto_perfil", schema="academia")

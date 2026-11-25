"""Endereço opcional da identidade. Revision 0028."""

import sqlalchemy as sa
from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("endereco", sa.String(300)), schema="academia")


def downgrade() -> None:
    op.drop_column("usuario", "endereco", schema="academia")

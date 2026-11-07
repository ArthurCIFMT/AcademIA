"""Cria o schema técnico para as tabelas do AcademIA."""

from alembic import op
from sqlalchemy.schema import CreateSchema, DropSchema

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(CreateSchema("academia"))


def downgrade() -> None:
    op.execute(DropSchema("academia"))

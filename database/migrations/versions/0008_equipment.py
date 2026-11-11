"""Create equipment inventory."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipamento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("categoria", sa.String(80), nullable=True),
        sa.Column("imagem_ref", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("operacional", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.CheckConstraint("length(btrim(nome)) > 0", name="ck_equipamento_nome"),
        sa.CheckConstraint("revision >= 1", name="ck_equipamento_revisao"),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("equipamento", schema="academia")

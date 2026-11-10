"""Store the primary instructor assignment and its history."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "designacao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("instrutor_id", sa.Uuid(), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atribuido_por", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["academia.cliente.usuario_id"]),
        sa.ForeignKeyConstraint(["instrutor_id"], ["academia.funcionario.usuario_id"]),
        sa.ForeignKeyConstraint(["atribuido_por"], ["academia.usuario.id"]),
        sa.CheckConstraint(
            "fim IS NULL OR fim >= inicio", name="ck_designacao_periodo"
        ),
        schema="academia",
    )
    op.create_index(
        "uq_designacao_cliente_vigente",
        "designacao",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("fim IS NULL"),
        schema="academia",
    )
    op.create_index(
        "ix_designacao_instrutor_vigente",
        "designacao",
        ["instrutor_id", "cliente_id"],
        postgresql_where=sa.text("fim IS NULL"),
        schema="academia",
    )
    op.create_index(
        "ix_designacao_cliente_inicio",
        "designacao",
        ["cliente_id", "inicio", "id"],
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("designacao", schema="academia")

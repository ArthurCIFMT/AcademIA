"""Referências faciais. Revision 0020."""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "biometria",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            nullable=False,
        ),
        sa.Column("subject_externo", sa.String(120), nullable=False, unique=True),
        sa.Column("image_id", sa.String(120), unique=True),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column(
            "cadastrada_por",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
            nullable=False,
        ),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(estado = 'PREPARANDO' AND image_id IS NULL) OR "
            "(estado IN ('PRONTA', 'ATIVA') AND image_id IS NOT NULL)",
            name="ck_biometria_referencia",
        ),
        schema="academia",
    )
    op.create_index(
        "uq_biometria_ativa_cliente",
        "biometria",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'ATIVA'"),
        schema="academia",
    )
    op.create_index(
        "uq_biometria_pendente_cliente",
        "biometria",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("estado IN ('PREPARANDO', 'PRONTA')"),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("biometria", schema="academia")

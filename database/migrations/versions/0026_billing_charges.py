"""Cobranças, revisões e vínculo financeiro opcional. Revision 0026."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_matricula_cliente_id", "matricula", ["id", "cliente_id"], schema="academia"
    )
    op.create_table(
        "cobranca",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            nullable=False,
        ),
        sa.Column("matricula_id", sa.Uuid()),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column("revisao", sa.Integer(), nullable=False),
        sa.CheckConstraint("valor >= 0", name="ck_cobranca_valor"),
        sa.CheckConstraint(
            "extract(day from competencia) = 1", name="ck_cobranca_competencia"
        ),
        sa.CheckConstraint(
            "estado IN ('ABERTA', 'CANCELADA')", name="ck_cobranca_estado"
        ),
        sa.CheckConstraint("revisao >= 1", name="ck_cobranca_revisao"),
        sa.UniqueConstraint("id", "cliente_id", name="uq_cobranca_cliente_id"),
        sa.ForeignKeyConstraint(
            ["matricula_id", "cliente_id"],
            ["academia.matricula.id", "academia.matricula.cliente_id"],
            name="fk_cobranca_matricula_cliente",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_cobranca_cliente_competencia",
        "cobranca",
        ["cliente_id", "competencia"],
        schema="academia",
    )
    op.create_table(
        "cobranca_revisao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cobranca_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cobranca.id"),
            nullable=False,
        ),
        sa.Column("revisao", sa.Integer(), nullable=False),
        sa.Column(
            "autor_id",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
            nullable=False,
        ),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dados", JSONB(), nullable=False),
        sa.CheckConstraint("revisao >= 1", name="ck_cobranca_revisao_numero"),
        sa.UniqueConstraint(
            "cobranca_id", "revisao", name="uq_cobranca_revisao_numero"
        ),
        schema="academia",
    )
    op.add_column("pagamento", sa.Column("cobranca_id", sa.Uuid()), schema="academia")
    op.create_foreign_key(
        "fk_pagamento_cobranca_cliente",
        "pagamento",
        "cobranca",
        ["cobranca_id", "cliente_id"],
        ["id", "cliente_id"],
        source_schema="academia",
        referent_schema="academia",
    )
    op.create_index(
        "ix_pagamento_cobranca", "pagamento", ["cobranca_id"], schema="academia"
    )


def downgrade() -> None:
    op.drop_index("ix_pagamento_cobranca", table_name="pagamento", schema="academia")
    op.drop_constraint(
        "fk_pagamento_cobranca_cliente",
        "pagamento",
        type_="foreignkey",
        schema="academia",
    )
    op.drop_column("pagamento", "cobranca_id", schema="academia")
    op.drop_table("cobranca_revisao", schema="academia")
    op.drop_table("cobranca", schema="academia")
    op.drop_constraint(
        "uq_matricula_cliente_id", "matricula", type_="unique", schema="academia"
    )

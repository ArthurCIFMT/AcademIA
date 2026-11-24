"""Registro manual e histórico de pagamentos. Revision 0025."""

import sqlalchemy as sa
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

_MANUAL_PAYMENT = """origem <> 'MANUAL' OR (
    referencia_externa IS NOT NULL
    AND referencia_externa = btrim(referencia_externa)
    AND referencia_externa <> ''
    AND valor > 0 AND estado IN ('CONFIRMADO', 'ANULADO')
    AND metodo IS NOT NULL
    AND metodo IN ('PIX', 'DINHEIRO', 'CARTAO', 'TRANSFERENCIA', 'OUTRO')
    AND pago_em IS NOT NULL AND confirmado_em IS NOT NULL
    AND registrado_por_id IS NOT NULL
    AND (
        (estado = 'CONFIRMADO' AND anulado_em IS NULL AND anulado_por_id IS NULL
         AND motivo_anulacao IS NULL)
        OR
        (estado = 'ANULADO' AND anulado_em IS NOT NULL AND anulado_por_id IS NOT NULL
         AND motivo_anulacao IS NOT NULL AND btrim(motivo_anulacao) <> ''
         AND anulado_em >= confirmado_em)
    )
)"""
_MANUAL_CONFIRMED = "origem = 'MANUAL' AND estado = 'CONFIRMADO'"
_REPLACEMENT = "substitui_id IS NULL OR (origem = 'MANUAL' AND substitui_id <> id)"


def upgrade() -> None:
    op.create_table(
        "pagamento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            nullable=False,
        ),
        sa.Column("plano_id", sa.Uuid(), sa.ForeignKey("academia.plano.id")),
        sa.Column("origem", sa.String(25), nullable=False),
        sa.Column("referencia_externa", sa.String(150)),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column("confirmado_em", sa.DateTime(timezone=True)),
        sa.Column("metodo", sa.String(25)),
        sa.Column("pago_em", sa.Date()),
        sa.Column(
            "registrado_por_id",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
        ),
        sa.Column("substitui_id", sa.Uuid(), unique=True),
        sa.Column(
            "anulado_por_id",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
        ),
        sa.Column("anulado_em", sa.DateTime(timezone=True)),
        sa.Column("motivo_anulacao", sa.String(240)),
        sa.CheckConstraint("valor >= 0", name="ck_pagamento_valor"),
        sa.CheckConstraint(_MANUAL_PAYMENT, name="ck_pagamento_manual"),
        sa.CheckConstraint(_REPLACEMENT, name="ck_pagamento_substituicao"),
        sa.UniqueConstraint("id", "cliente_id", name="uq_pagamento_cliente_id"),
        sa.ForeignKeyConstraint(
            ["substitui_id", "cliente_id"],
            ["academia.pagamento.id", "academia.pagamento.cliente_id"],
            name="fk_pagamento_substituido_cliente",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_pagamento_cliente", "pagamento", ["cliente_id"], schema="academia"
    )
    op.create_index(
        "uq_pagamento_manual_referencia",
        "pagamento",
        [sa.text("lower(referencia_externa)")],
        unique=True,
        schema="academia",
        postgresql_where=sa.text(_MANUAL_CONFIRMED),
    )


def downgrade() -> None:
    op.drop_table("pagamento", schema="academia")

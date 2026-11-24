"""Eventos de identificação facial. Revision 0021."""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evento_acesso",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("origem", sa.String(80), nullable=False),
        sa.Column("event_id_externo", sa.String(120), nullable=False),
        sa.Column(
            "cliente_id", sa.Uuid(), sa.ForeignKey("academia.cliente.usuario_id")
        ),
        sa.Column("tipo", sa.String(25), nullable=False),
        sa.Column("ocorrido_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.CHAR(64), nullable=False),
        sa.Column("direcao", sa.String(10), nullable=False),
        sa.Column("resultado_identificacao", sa.String(24)),
        sa.Column("similaridade", sa.Float()),
        sa.UniqueConstraint(
            "origem", "event_id_externo", name="uq_evento_acesso_origem_id"
        ),
        sa.CheckConstraint(
            "direcao IN ('ENTRADA', 'SAIDA')", name="ck_evento_acesso_direcao"
        ),
        sa.CheckConstraint(
            "similaridade BETWEEN 0 AND 1", name="ck_evento_acesso_similaridade"
        ),
        sa.CheckConstraint(
            """tipo <> 'IDENTIFICACAO' OR (
                resultado_identificacao IS NOT NULL
                AND resultado_identificacao IN (
                    'IDENTIFICADO', 'DESCONHECIDO', 'PONTUACAO_BAIXA', 'AMBIGUO',
                    'CAPTURA_INVALIDA', 'FALHA_PROVEDOR'
                )
                AND ((resultado_identificacao = 'IDENTIFICADO')
                     = (cliente_id IS NOT NULL))
                AND (resultado_identificacao <> 'IDENTIFICADO'
                     OR similaridade IS NOT NULL)
            )""",
            name="ck_evento_acesso_identificacao",
        ),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("evento_acesso", schema="academia")

"""Confirmação manual vinculada a falha facial. Revision 0023."""

import sqlalchemy as sa
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

_MANUAL_EVENT = """tipo <> 'IDENTIFICACAO_MANUAL' OR (
    origem = 'ATENDIMENTO_MANUAL' AND cliente_id IS NOT NULL AND similaridade IS NULL
    AND resultado_identificacao IS NOT NULL AND resultado_identificacao = 'IDENTIFICADO'
)"""


def upgrade() -> None:
    op.create_check_constraint(
        "ck_evento_acesso_manual", "evento_acesso", _MANUAL_EVENT, schema="academia"
    )
    op.create_table(
        "identificacao_manual",
        sa.Column(
            "evento_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            primary_key=True,
        ),
        sa.Column(
            "evento_falha_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "atendente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
            nullable=False,
        ),
        sa.Column("motivo", sa.String(240), nullable=False),
        sa.CheckConstraint(
            "btrim(motivo) <> ''", name="ck_identificacao_manual_motivo"
        ),
        sa.CheckConstraint(
            "evento_id <> evento_falha_id", name="ck_identificacao_manual_eventos"
        ),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("identificacao_manual", schema="academia")
    op.drop_constraint(
        "ck_evento_acesso_manual", "evento_acesso", type_="check", schema="academia"
    )

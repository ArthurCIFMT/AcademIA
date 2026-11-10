"""Persist internal notices and email delivery state."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notificacao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("destinatario_id", sa.Uuid(), nullable=False),
        sa.Column("evento_id", sa.Uuid(), nullable=False),
        sa.Column("canal", sa.String(25), nullable=False),
        sa.Column("tipo", sa.String(25), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column("tentativas", sa.Integer(), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["destinatario_id"], ["academia.usuario.id"]),
        sa.UniqueConstraint(
            "destinatario_id", "evento_id", "canal", name="uq_notificacao_dest_evento_canal"
        ),
        sa.CheckConstraint(
            "(canal = 'INTERNO' AND estado = 'PENDENTE' AND tentativas = 0 "
            "AND tipo IN ('TREINO_PARA_AVALIAR', 'ALTERACAO_CRITICA')) OR "
            "(canal = 'EMAIL' AND estado IN "
            "('ENVIANDO', 'ENVIADO', 'FALHOU', 'INCERTO') "
            "AND tentativas BETWEEN 1 AND 3 AND lida_em IS NULL "
            "AND tipo IN ('PRIMEIRO_ACESSO', 'RECUPERACAO', 'CONVITE_ONBOARDING', "
            "'TREINO_PARA_AVALIAR', 'ALTERACAO_CRITICA'))",
            name="ck_notificacao_fluxo",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_notificacao_lista",
        "notificacao",
        ["destinatario_id", "canal", "criada_em", "id"],
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("notificacao", schema="academia")

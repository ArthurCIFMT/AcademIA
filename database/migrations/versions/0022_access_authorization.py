"""Decisões de acesso e comandos da catraca. Revision 0022."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decisao_acesso",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "evento_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("matricula_id", sa.Uuid(), sa.ForeignKey("academia.matricula.id")),
        sa.Column("resultado", sa.String(15), nullable=False),
        sa.Column("motivo", sa.String(80), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regra_json", JSONB(), nullable=False),
        sa.CheckConstraint(
            "resultado IN ('ALLOW', 'DENY')", name="ck_decisao_acesso_resultado"
        ),
        schema="academia",
    )
    op.create_table(
        "catraca_comando",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "decisao_id",
            sa.Uuid(),
            sa.ForeignKey("academia.decisao_acesso.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("request_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("direcao", sa.String(15), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column(
            "passagem_evento_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            unique=True,
        ),
        sa.Column("falha_envio", sa.String(25)),
        sa.CheckConstraint("direcao IN ('ENTRY', 'EXIT')", name="ck_catraca_direcao"),
        sa.CheckConstraint(
            "estado IN ('CRIADO', 'ACEITO', 'FALHOU', 'CONFIRMADO')",
            name="ck_catraca_estado",
        ),
        sa.CheckConstraint(
            "(estado = 'CONFIRMADO') = (passagem_evento_id IS NOT NULL)",
            name="ck_catraca_passagem",
        ),
        sa.CheckConstraint(
            "(estado = 'FALHOU') = (falha_envio IS NOT NULL)", name="ck_catraca_falha"
        ),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("catraca_comando", schema="academia")
    op.drop_table("decisao_acesso", schema="academia")

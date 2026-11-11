"""Publicação técnica e parecer conclusivo imutável.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "validacao_ficha",
        sa.Column("versao_id", sa.Uuid(), primary_key=True),
        sa.Column("solicitacao_id", sa.Uuid(), nullable=False),
        sa.Column("validado_por", sa.Uuid(), nullable=False),
        sa.Column("revisao", sa.Integer(), nullable=False),
        sa.Column("restricoes_conferidas", sa.Boolean(), nullable=False),
        sa.Column("validado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["versao_id"], ["academia.versao_ficha.id"]),
        sa.ForeignKeyConstraint(["validado_por"], ["academia.usuario.id"]),
        sa.CheckConstraint(
            "revisao >= 1 AND restricoes_conferidas", name="ck_validacao_ficha"
        ),
        schema="academia",
    )
    op.create_index(
        "uq_parecer_conclusivo",
        "parecer",
        ["versao_id"],
        unique=True,
        postgresql_where=sa.text("estado <> 'PENDENTE'"),
        schema="academia",
    )
    op.create_check_constraint(
        "ck_parecer_rejeicao_motivo",
        "parecer",
        "estado <> 'REJEITADO' OR length(btrim(motivo)) > 0 AND motivo IS NOT NULL",
        schema="academia",
    )
    op.execute("""
        CREATE FUNCTION academia.proteger_validacao_parecer() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Registro técnico/profissional imutável';
        END $$;
        CREATE TRIGGER proteger_validacao_ficha
        BEFORE UPDATE OR DELETE ON academia.validacao_ficha
        FOR EACH ROW EXECUTE FUNCTION academia.proteger_validacao_parecer();
        CREATE TRIGGER proteger_parecer_ficha
        BEFORE UPDATE OR DELETE ON academia.parecer
        FOR EACH ROW EXECUTE FUNCTION academia.proteger_validacao_parecer();
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER proteger_parecer_ficha ON academia.parecer;
        DROP TRIGGER proteger_validacao_ficha ON academia.validacao_ficha;
        DROP FUNCTION academia.proteger_validacao_parecer();
    """)
    op.drop_constraint("ck_parecer_rejeicao_motivo", "parecer", schema="academia")
    op.drop_index("uq_parecer_conclusivo", table_name="parecer", schema="academia")
    op.drop_table("validacao_ficha", schema="academia")

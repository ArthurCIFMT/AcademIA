"""Planos e matrículas. Revision 0019."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plano",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("duracao_dias", sa.Integer(), nullable=False),
        sa.Column("modalidade", sa.String(80), nullable=False),
        sa.Column("limite_acessos", sa.Integer()),
        sa.Column("janela_limite", sa.String(25)),
        sa.Column("preco_base", sa.Numeric(12, 2)),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.CheckConstraint("btrim(nome) <> ''", name="ck_plano_nome"),
        sa.CheckConstraint("btrim(modalidade) <> ''", name="ck_plano_modalidade"),
        sa.CheckConstraint("duracao_dias > 0", name="ck_plano_duracao"),
        sa.CheckConstraint("limite_acessos > 0", name="ck_plano_limite"),
        sa.CheckConstraint(
            "(limite_acessos IS NULL AND janela_limite IS NULL) OR "
            "(limite_acessos IS NOT NULL AND janela_limite IS NOT NULL "
            "AND janela_limite = 'DIA_CIVIL')",
            name="ck_plano_janela",
        ),
        sa.CheckConstraint("preco_base >= 0", name="ck_plano_preco"),
        sa.CheckConstraint("revision >= 1", name="ck_plano_revision"),
        schema="academia",
    )
    op.create_table(
        "matricula",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "plano_id", sa.Uuid(), sa.ForeignKey("academia.plano.id"), nullable=False
        ),
        sa.Column(
            "atendente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.funcionario.usuario_id"),
            nullable=False,
        ),
        sa.Column("inicio", sa.Date(), nullable=False),
        sa.Column("fim", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("modalidade_contratada", sa.String(80), nullable=False),
        sa.Column("limites_snapshot", JSONB(), nullable=False),
        sa.CheckConstraint("fim >= inicio", name="ck_matricula_periodo"),
        sa.CheckConstraint(
            "estado IN ('ATIVA', 'ENCERRADA')", name="ck_matricula_estado"
        ),
        sa.CheckConstraint(
            "btrim(modalidade_contratada) <> ''", name="ck_matricula_modalidade"
        ),
        sa.CheckConstraint(
            """jsonb_typeof(limites_snapshot) = 'object'
            AND limites_snapshot ?& array['limite_acessos', 'janela_limite']
            AND CASE jsonb_typeof(limites_snapshot -> 'limite_acessos')
                WHEN 'null' THEN limites_snapshot -> 'janela_limite' = 'null'::jsonb
                WHEN 'number' THEN
                    limites_snapshot ->> 'limite_acessos' ~ '^[1-9][0-9]*$'
                    AND limites_snapshot -> 'janela_limite' = '"DIA_CIVIL"'::jsonb
                ELSE false END""",
            name="ck_matricula_limites",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_matricula_cliente_periodo",
        "matricula",
        ["cliente_id", "inicio", "fim"],
        schema="academia",
    )
    op.create_index("ix_matricula_plano", "matricula", ["plano_id"], schema="academia")


def downgrade() -> None:
    op.drop_table("matricula", schema="academia")
    op.drop_table("plano", schema="academia")

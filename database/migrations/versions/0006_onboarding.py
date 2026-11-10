"""Persist onboarding drafts, immutable snapshots and evaluations."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_versao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("idade_snapshot", sa.Integer(), nullable=True),
        sa.Column("dados", JSONB(), nullable=False),
        sa.Column("criado_por", sa.Uuid(), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("concluido_por", sa.Uuid(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["academia.cliente.usuario_id"]),
        sa.ForeignKeyConstraint(["criado_por"], ["academia.usuario.id"]),
        sa.ForeignKeyConstraint(["concluido_por"], ["academia.usuario.id"]),
        sa.UniqueConstraint(
            "cliente_id", "numero", name="uq_onboarding_cliente_numero"
        ),
        sa.UniqueConstraint("cliente_id", "id", name="uq_onboarding_cliente_id"),
        sa.CheckConstraint(
            "numero >= 1 AND revision >= 1 AND schema_version = 1",
            name="ck_onboarding_versoes",
        ),
        sa.CheckConstraint(
            "(estado = 'RASCUNHO' AND idade_snapshot IS NULL AND concluido_em IS NULL "
            "AND concluido_por IS NULL) OR "
            "(estado = 'CONCLUIDO' AND idade_snapshot IS NOT NULL "
            "AND idade_snapshot >= 0 "
            "AND concluido_em IS NOT NULL AND concluido_por IS NOT NULL)",
            name="ck_onboarding_estado",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(dados) = 'object'", name="ck_onboarding_dados"
        ),
        schema="academia",
    )
    op.create_index(
        "uq_onboarding_cliente_rascunho",
        "onboarding_versao",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'RASCUNHO'"),
        schema="academia",
    )
    op.create_table(
        "avaliacao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("instrutor_id", sa.Uuid(), nullable=False),
        sa.Column("onboarding_id", sa.Uuid(), nullable=False),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dados", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["academia.cliente.usuario_id"]),
        sa.ForeignKeyConstraint(["instrutor_id"], ["academia.funcionario.usuario_id"]),
        sa.ForeignKeyConstraint(
            ["cliente_id", "onboarding_id"],
            ["academia.onboarding_versao.cliente_id", "academia.onboarding_versao.id"],
            name="fk_avaliacao_onboarding_cliente",
        ),
        sa.CheckConstraint("jsonb_typeof(dados) = 'object'", name="ck_avaliacao_dados"),
        schema="academia",
    )
    op.create_index(
        "ix_avaliacao_cliente_registro",
        "avaliacao",
        ["cliente_id", "registrado_em", "id"],
        schema="academia",
    )
    op.execute("""
        CREATE FUNCTION academia.proteger_versao_concluida() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.estado = 'CONCLUIDO' THEN
                RAISE EXCEPTION 'Versão concluída de onboarding é imutável.'
                    USING ERRCODE = '55000';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER proteger_versao_concluida BEFORE UPDATE OR DELETE
        ON academia.onboarding_versao FOR EACH ROW
        EXECUTE FUNCTION academia.proteger_versao_concluida()
    """)
    op.execute("""
        CREATE FUNCTION academia.proteger_avaliacao() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Avaliações são registradas como histórico imutável.'
                USING ERRCODE = '55000';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER proteger_avaliacao BEFORE UPDATE OR DELETE
        ON academia.avaliacao FOR EACH ROW EXECUTE FUNCTION academia.proteger_avaliacao()
    """)


def downgrade() -> None:
    op.drop_table("avaliacao", schema="academia")
    op.drop_table("onboarding_versao", schema="academia")
    op.execute("DROP FUNCTION academia.proteger_avaliacao()")
    op.execute("DROP FUNCTION academia.proteger_versao_concluida()")

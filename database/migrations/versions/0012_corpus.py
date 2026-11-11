"""Documentos e versões do corpus com decisões rastreáveis."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ambiente", sa.String(15), nullable=False),
        sa.Column("catalogo_id", sa.String(40), nullable=False),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("origem_url", sa.Text(), nullable=False),
        sa.Column("licenca", sa.Text(), nullable=False),
        sa.UniqueConstraint("ambiente", "catalogo_id", name="uq_documento_catalogo"),
        sa.UniqueConstraint("id", "ambiente", name="uq_documento_ambiente"),
        sa.CheckConstraint(
            "ambiente IN ('LITERATURA','TESTE')", name="ck_documento_ambiente"
        ),
        schema="academia",
    )
    op.create_table(
        "documento_versao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("documento_id", sa.Uuid(), nullable=False),
        sa.Column("ambiente", sa.String(15), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("idioma", sa.String(12), nullable=False),
        sa.Column("arquivo_ref", sa.Text(), nullable=False),
        sa.Column("formato", sa.String(3), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("metadados", JSONB(), nullable=False),
        sa.Column(
            "criado_por",
            sa.Uuid(),
            sa.ForeignKey("academia.usuario.id"),
            nullable=False,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column("aprovado_por", sa.Uuid(), sa.ForeignKey("academia.usuario.id")),
        sa.Column("aprovado_em", sa.DateTime(timezone=True)),
        sa.Column("revogado_por", sa.Uuid(), sa.ForeignKey("academia.usuario.id")),
        sa.Column("revogado_em", sa.DateTime(timezone=True)),
        sa.Column("motivo_revogacao", sa.Text()),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["documento_id", "ambiente"],
            ["academia.documento.id", "academia.documento.ambiente"],
            name="fk_documento_versao_ambiente",
        ),
        sa.UniqueConstraint("documento_id", "numero", name="uq_documento_numero"),
        sa.UniqueConstraint("ambiente", "sha256", name="uq_documento_hash"),
        sa.CheckConstraint(
            "numero >= 1 AND revision >= 1 AND tamanho_bytes > 0 AND formato IN "
            "('PDF','TXT') AND jsonb_typeof(metadados) = 'object'",
            name="ck_documento_conteudo",
        ),
        sa.CheckConstraint(
            "estado IN ('PENDENTE','APROVADO','REVOGADO') AND "
            "((estado = 'PENDENTE' AND aprovado_por IS NULL AND aprovado_em IS NULL) "
            "OR "
            "(estado <> 'PENDENTE' AND aprovado_por IS NOT NULL AND aprovado_em IS "
            "NOT NULL)) AND "
            "((estado = 'REVOGADO' AND revogado_por IS NOT NULL AND revogado_em IS "
            "NOT NULL AND motivo_revogacao IS NOT NULL AND "
            "length(btrim(motivo_revogacao)) > 0) OR "
            "(estado <> 'REVOGADO' AND revogado_por IS NULL AND revogado_em IS NULL "
            "AND motivo_revogacao IS NULL))",
            name="ck_documento_aprovacao",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_documento_uso",
        "documento_versao",
        ["ambiente", "estado"],
        schema="academia",
    )
    op.execute("""
    CREATE FUNCTION academia.proteger_corpus() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF TG_OP = 'DELETE' OR TG_TABLE_NAME = 'documento' THEN
            RAISE EXCEPTION 'Proveniência documental imutável';
        END IF;
        IF (to_jsonb(NEW) - ARRAY['estado','aprovado_por','aprovado_em',
                'revogado_por','revogado_em','motivo_revogacao','revision'])
            IS DISTINCT FROM
           (to_jsonb(OLD) - ARRAY['estado','aprovado_por','aprovado_em',
                'revogado_por','revogado_em','motivo_revogacao','revision'])
           OR NEW.revision <> OLD.revision + 1
           OR NOT ((OLD.estado = 'PENDENTE' AND NEW.estado = 'APROVADO') OR
                   (OLD.estado = 'APROVADO' AND NEW.estado = 'REVOGADO'))
           OR (OLD.estado = 'APROVADO' AND
               (NEW.aprovado_por IS DISTINCT FROM OLD.aprovado_por
                OR NEW.aprovado_em IS DISTINCT FROM OLD.aprovado_em))
        THEN RAISE EXCEPTION 'Versão documental imutável'; END IF;
        RETURN NEW;
    END $$;
    CREATE TRIGGER proteger_documento BEFORE UPDATE OR DELETE ON academia.documento
    FOR EACH ROW EXECUTE FUNCTION academia.proteger_corpus();
    CREATE TRIGGER proteger_documento_versao BEFORE UPDATE OR DELETE
    ON academia.documento_versao
    FOR EACH ROW EXECUTE FUNCTION academia.proteger_corpus();
    """)


def downgrade() -> None:
    op.execute("""
    DROP TRIGGER proteger_documento_versao ON academia.documento_versao;
    DROP TRIGGER proteger_documento ON academia.documento;
    DROP FUNCTION academia.proteger_corpus();
    """)
    op.drop_index("ix_documento_uso", table_name="documento_versao", schema="academia")
    op.drop_table("documento_versao", schema="academia")
    op.drop_table("documento", schema="academia")

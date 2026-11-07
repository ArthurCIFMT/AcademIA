"""Cria auditoria e fila transacional de eventos."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ator_id", sa.Uuid()),
        sa.Column("acao", sa.String(80), nullable=False),
        sa.Column("recurso_tipo", sa.String(60), nullable=False),
        sa.Column("recurso_id", sa.Uuid()),
        sa.Column("motivo", sa.Text()),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("ocorrido_em", sa.DateTime(timezone=True), nullable=False),
        schema="academia",
    )
    op.execute(
        """
        CREATE FUNCTION academia.proteger_auditoria() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Registros de auditoria são imutáveis'
                USING ERRCODE = '42501';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER proteger_auditoria
        BEFORE UPDATE OR DELETE OR TRUNCATE ON academia.auditoria
        FOR EACH STATEMENT EXECUTE FUNCTION academia.proteger_auditoria()
        """
    )
    op.create_table(
        "outbox",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("evento_tipo", sa.String(80), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("entregue_em", sa.DateTime(timezone=True)),
        sa.CheckConstraint("schema_version > 0", name="ck_outbox_schema_version"),
        sa.CheckConstraint(
            "(estado = 'PENDENTE' AND entregue_em IS NULL) OR "
            "(estado = 'ENTREGUE' AND entregue_em IS NOT NULL)",
            name="ck_outbox_entrega",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_outbox_pendentes",
        "outbox",
        ["criado_em", "id"],
        postgresql_where=sa.text("estado = 'PENDENTE'"),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("outbox", schema="academia")
    op.drop_table("auditoria", schema="academia")
    op.execute("DROP FUNCTION academia.proteger_auditoria()")

"""Conversa e mensagens privadas. Revision 0015."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversa",
        sa.Column(
            "id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            primary_key=True,
        ),
        schema="academia",
    )
    op.create_table(
        "mensagem",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversa_id",
            sa.Uuid(),
            sa.ForeignKey("academia.conversa.id"),
            nullable=False,
        ),
        sa.Column("solicitacao_id", sa.Uuid(), nullable=False),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False),
        sa.Column("erro_codigo", sa.Text()),
        sa.Column("pedido", JSONB(), nullable=False),
        sa.Column(
            "versao_contexto_id", sa.Uuid(), sa.ForeignKey("academia.versao_ficha.id")
        ),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("conversa_id", "solicitacao_id", name="uq_mensagem_pedido"),
        sa.CheckConstraint(
            "length(btrim(pergunta)) BETWEEN 1 AND 1000 AND jsonb_typeof(pedido) = 'object'",
            name="ck_mensagem_pergunta",
        ),
        sa.ForeignKeyConstraint(
            ["conversa_id", "versao_contexto_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
            name="fk_mensagem_ficha_contexto",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_mensagem_historico",
        "mensagem",
        ["conversa_id", "criada_em"],
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("mensagem", schema="academia")
    op.drop_table("conversa", schema="academia")

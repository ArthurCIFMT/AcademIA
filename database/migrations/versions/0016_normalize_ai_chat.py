"""Fontes únicas de dados IA/chat, preservando contratos. Revision 0016."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

TOKEN_CHECK = (
    "(tokens_entrada IS NULL AND tokens_saida IS NULL) OR "
    "(tokens_entrada IS NOT NULL AND tokens_saida IS NOT NULL "
    "AND tokens_entrada >= 0 AND tokens_saida >= 0)"
)
QUESTION_CHECK = (
    "jsonb_typeof(pedido) = 'object' AND pedido ? 'mensagem' "
    "AND jsonb_typeof(pedido->'mensagem') = 'string' "
    "AND length(btrim(pedido->>'mensagem')) BETWEEN 1 AND 1000"
)
CONSUMPTION = """jsonb_build_object(
    'etapa', tipo, 'chamadas_fisicas', chamadas,
    'limite_saida_tokens', limite_saida_tokens, 'prompt_bytes', prompt_bytes,
    'prompt_sha256', prompt_sha256,
    'uso', CASE WHEN tokens_entrada IS NULL THEN NULL ELSE jsonb_build_object(
        'prompt_tokens', tokens_entrada, 'completion_tokens', tokens_saida,
        'total_tokens', tokens_entrada + tokens_saida) END,
    'consumo_desconhecido', tokens_entrada IS NULL)"""


def upgrade() -> None:
    # Não escolher silenciosamente entre cópias divergentes nem emitir conteúdo
    # privado no erro. Todos os gates antecedem a primeira alteração de schema.
    op.execute(
        sa.text(
            """DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM academia.mensagem WHERE
                pergunta IS DISTINCT FROM pedido->>'mensagem'
                OR NOT COALESCE("""
            + QUESTION_CHECK
            + """, false)) THEN
                RAISE EXCEPTION
                    '0016: pedido de mensagem incoerente; nenhuma copia descartada';
            END IF;
            IF EXISTS (SELECT 1 FROM academia.etapa_ia WHERE NOT ("""
            + TOKEN_CHECK
            + """)) OR EXISTS (SELECT 1 FROM academia.etapa_ia WHERE
                dados IS DISTINCT FROM """
            + CONSUMPTION
            + """) THEN
                RAISE EXCEPTION
                    '0016: consumo de etapa incoerente; nenhuma copia descartada';
            END IF;
            IF EXISTS (SELECT 1 FROM academia.triagem t
                JOIN academia.execucao_ia e ON e.id=t.execucao_id
                WHERE t.resumo IS DISTINCT FROM
                    COALESCE(NULLIF(e.resultado->'triagem', 'null'::jsonb),
                             '{}'::jsonb)) THEN
                RAISE EXCEPTION '0016: triagem incoerente; nenhuma copia descartada';
            END IF;
            END $$"""
        )
    )
    # O JSON de consumo da execução já era projeção sobrescrita na leitura;
    # durante uma execução em voo pode estar desatualizado. Etapas são canônicas.
    op.execute("UPDATE academia.execucao_ia SET resultado = resultado - 'consumo'")
    op.drop_column("triagem", "resumo", schema="academia")
    op.drop_column("etapa_ia", "dados", schema="academia")
    op.create_check_constraint(
        "ck_etapa_tokens", "etapa_ia", TOKEN_CHECK, schema="academia"
    )

    for fk in sa.inspect(op.get_bind()).get_foreign_keys("mensagem", schema="academia"):
        if fk["constrained_columns"] in (["conversa_id"], ["versao_contexto_id"]):
            op.drop_constraint(
                fk["name"], "mensagem", type_="foreignkey", schema="academia"
            )
    op.alter_column(
        "mensagem", "conversa_id", new_column_name="cliente_id", schema="academia"
    )
    op.create_foreign_key(
        "fk_mensagem_cliente",
        "mensagem",
        "cliente",
        ["cliente_id"],
        ["usuario_id"],
        source_schema="academia",
        referent_schema="academia",
    )
    # A FK composta de cliente/contexto continua existente e garante titularidade.
    op.drop_constraint(
        "ck_mensagem_pergunta", "mensagem", type_="check", schema="academia"
    )
    op.drop_column("mensagem", "pergunta", schema="academia")
    op.create_check_constraint(
        "ck_mensagem_pergunta", "mensagem", QUESTION_CHECK, schema="academia"
    )
    op.drop_table("conversa", schema="academia")


def downgrade() -> None:
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
    op.execute(
        "INSERT INTO academia.conversa (id) "
        "SELECT DISTINCT cliente_id FROM academia.mensagem"
    )
    op.drop_constraint(
        "fk_mensagem_cliente", "mensagem", type_="foreignkey", schema="academia"
    )
    op.alter_column(
        "mensagem", "cliente_id", new_column_name="conversa_id", schema="academia"
    )
    op.create_foreign_key(
        "mensagem_conversa_id_fkey",
        "mensagem",
        "conversa",
        ["conversa_id"],
        ["id"],
        source_schema="academia",
        referent_schema="academia",
    )
    op.create_foreign_key(
        "mensagem_versao_contexto_id_fkey",
        "mensagem",
        "versao_ficha",
        ["versao_contexto_id"],
        ["id"],
        source_schema="academia",
        referent_schema="academia",
    )
    op.drop_constraint(
        "ck_mensagem_pergunta", "mensagem", type_="check", schema="academia"
    )
    op.add_column(
        "mensagem", sa.Column("pergunta", sa.Text(), nullable=True), schema="academia"
    )
    op.execute("UPDATE academia.mensagem SET pergunta = pedido->>'mensagem'")
    op.alter_column("mensagem", "pergunta", nullable=False, schema="academia")
    op.create_check_constraint(
        "ck_mensagem_pergunta",
        "mensagem",
        "length(btrim(pergunta)) BETWEEN 1 AND 1000 "
        "AND jsonb_typeof(pedido) = 'object'",
        schema="academia",
    )
    op.add_column(
        "triagem", sa.Column("resumo", JSONB(), nullable=True), schema="academia"
    )
    op.execute("""UPDATE academia.triagem t SET resumo =
        COALESCE(NULLIF(e.resultado->'triagem', 'null'::jsonb), '{}'::jsonb)
        FROM academia.execucao_ia e WHERE e.id=t.execucao_id""")
    op.alter_column("triagem", "resumo", nullable=False, schema="academia")
    op.add_column(
        "etapa_ia", sa.Column("dados", JSONB(), nullable=True), schema="academia"
    )
    op.execute("UPDATE academia.etapa_ia SET dados = " + CONSUMPTION)
    op.alter_column("etapa_ia", "dados", nullable=False, schema="academia")
    op.drop_constraint("ck_etapa_tokens", "etapa_ia", type_="check", schema="academia")
    op.execute("""UPDATE academia.execucao_ia e SET resultado = jsonb_set(
        resultado, '{consumo}', COALESCE((SELECT jsonb_agg(s.dados ORDER BY s.tipo)
        FROM academia.etapa_ia s WHERE s.execucao_id=e.id), '[]'::jsonb))""")

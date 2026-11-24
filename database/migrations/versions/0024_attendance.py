"""Frequência e lotação a partir de passagens confirmadas. Revision 0024."""

import sqlalchemy as sa
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

_CONFIRMED_PASSAGE = "tipo = 'PASSAGEM_SIMULADA' AND origem = 'CATRACA_SIMULADA'"
_OUTCOME = f"""resultado_presenca IS NULL OR (
    {_CONFIRMED_PASSAGE} AND cliente_id IS NOT NULL
    AND resultado_presenca IN (
        'ENTRADA_REGISTRADA', 'SAIDA_REGISTRADA',
        'ENTRADA_REPETIDA', 'SAIDA_SEM_ENTRADA'
    )
)"""


def upgrade() -> None:
    op.add_column(
        "evento_acesso",
        sa.Column("resultado_presenca", sa.String(24)),
        schema="academia",
    )
    op.create_check_constraint(
        "ck_evento_acesso_resultado_presenca",
        "evento_acesso",
        _OUTCOME,
        schema="academia",
    )
    op.create_index(
        "ix_evento_acesso_passagem_cliente",
        "evento_acesso",
        ["cliente_id", "ocorrido_em", "id"],
        schema="academia",
        postgresql_where=sa.text(_CONFIRMED_PASSAGE),
    )
    op.create_table(
        "presenca",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cliente_id",
            sa.Uuid(),
            sa.ForeignKey("academia.cliente.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "entrada_evento_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "saida_evento_id",
            sa.Uuid(),
            sa.ForeignKey("academia.evento_acesso.id"),
            unique=True,
        ),
        sa.CheckConstraint(
            "id = entrada_evento_id AND entrada_evento_id <> saida_evento_id",
            name="ck_presenca_eventos",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_presenca_cliente", "presenca", ["cliente_id"], schema="academia"
    )
    op.create_index(
        "uq_presenca_cliente_aberta",
        "presenca",
        ["cliente_id"],
        unique=True,
        schema="academia",
        postgresql_where=sa.text("saida_evento_id IS NULL"),
    )
    op.execute(
        sa.text("""
        WITH ordenadas AS (
            SELECT e.id, e.direcao, lag(e.direcao) OVER (
                PARTITION BY e.cliente_id ORDER BY e.ocorrido_em,
                CASE WHEN e.direcao = 'ENTRADA' THEN 0 ELSE 1 END, e.id
            ) AS anterior
            FROM academia.evento_acesso AS e
            JOIN academia.catraca_comando AS c
                ON c.passagem_evento_id = e.id AND c.estado = 'CONFIRMADO'
            WHERE e.tipo = 'PASSAGEM_SIMULADA' AND e.origem = 'CATRACA_SIMULADA'
                AND e.cliente_id IS NOT NULL
        )
        UPDATE academia.evento_acesso AS e
        SET resultado_presenca = CASE
            WHEN o.direcao = 'ENTRADA' AND o.anterior = 'ENTRADA'
                THEN 'ENTRADA_REPETIDA'
            WHEN o.direcao = 'ENTRADA' THEN 'ENTRADA_REGISTRADA'
            WHEN o.anterior = 'ENTRADA' THEN 'SAIDA_REGISTRADA'
            ELSE 'SAIDA_SEM_ENTRADA'
        END
        FROM ordenadas AS o WHERE o.id = e.id
    """)
    )
    op.execute(
        sa.text("""
        WITH pareadas AS (
            SELECT id, cliente_id, resultado_presenca, lead(id) OVER (
                PARTITION BY cliente_id ORDER BY ocorrido_em,
                CASE WHEN direcao = 'ENTRADA' THEN 0 ELSE 1 END, id
            ) AS evento_seguinte
            FROM academia.evento_acesso
            WHERE resultado_presenca IN ('ENTRADA_REGISTRADA', 'SAIDA_REGISTRADA')
        )
        INSERT INTO academia.presenca
            (id, cliente_id, entrada_evento_id, saida_evento_id)
        SELECT id, cliente_id, id, evento_seguinte
        FROM pareadas WHERE resultado_presenca = 'ENTRADA_REGISTRADA'
    """)
    )


def downgrade() -> None:
    op.drop_table("presenca", schema="academia")
    op.drop_index(
        "ix_evento_acesso_passagem_cliente",
        table_name="evento_acesso",
        schema="academia",
    )
    op.drop_constraint(
        "ck_evento_acesso_resultado_presenca",
        "evento_acesso",
        type_="check",
        schema="academia",
    )
    op.drop_column("evento_acesso", "resultado_presenca", schema="academia")

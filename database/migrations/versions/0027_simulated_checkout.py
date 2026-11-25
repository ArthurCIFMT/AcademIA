"""Histórico e invariantes da compra simulada. Revision 0027."""

import sqlalchemy as sa
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pagamento", sa.Column("plano_nome_snapshot", sa.String(100)), schema="academia"
    )
    op.add_column(
        "pagamento",
        sa.Column("simulado_em", sa.DateTime(timezone=True)),
        schema="academia",
    )
    op.create_check_constraint(
        "ck_pagamento_simulacao",
        "pagamento",
        """(
            origem = 'SIMULACAO'
            AND plano_id IS NOT NULL
            AND plano_nome_snapshot IS NOT NULL AND btrim(plano_nome_snapshot) <> ''
            AND simulado_em IS NOT NULL
            AND (
                (estado = 'CONFIRMADO' AND confirmado_em = simulado_em
                 AND confirmado_em IS NOT NULL AND pago_em IS NOT NULL)
                OR (estado IN ('PENDENTE', 'RECUSADO') AND confirmado_em IS NULL
                    AND pago_em IS NULL)
            )
        ) OR (origem <> 'SIMULACAO' AND plano_nome_snapshot IS NULL
              AND simulado_em IS NULL)""",
        schema="academia",
    )
    op.create_index(
        "ix_pagamento_historico_simulacao",
        "pagamento",
        ["cliente_id", "simulado_em", "id"],
        schema="academia",
        postgresql_where=sa.text("origem = 'SIMULACAO'"),
    )


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM academia.pagamento WHERE origem = 'SIMULACAO') THEN
                RAISE EXCEPTION 'Downgrade removeria o histórico de simulações.';
            END IF;
        END $$;
    """)
    op.drop_index(
        "ix_pagamento_historico_simulacao", table_name="pagamento", schema="academia"
    )
    op.drop_constraint(
        "ck_pagamento_simulacao", "pagamento", type_="check", schema="academia"
    )
    op.drop_column("pagamento", "simulado_em", schema="academia")
    op.drop_column("pagamento", "plano_nome_snapshot", schema="academia")

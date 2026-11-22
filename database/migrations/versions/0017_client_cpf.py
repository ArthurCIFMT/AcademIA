"""CPF opcional no cadastro de clientes. Revision 0017."""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cliente", sa.Column("cpf", sa.String(11), nullable=True), schema="academia"
    )
    op.create_check_constraint(
        "ck_cliente_cpf_formato", "cliente", "cpf ~ '^[0-9]{11}$'", schema="academia"
    )
    op.create_unique_constraint("uq_cliente_cpf", "cliente", ["cpf"], schema="academia")


def downgrade() -> None:
    op.drop_constraint("uq_cliente_cpf", "cliente", type_="unique", schema="academia")
    op.drop_constraint(
        "ck_cliente_cpf_formato", "cliente", type_="check", schema="academia"
    )
    op.drop_column("cliente", "cpf", schema="academia")

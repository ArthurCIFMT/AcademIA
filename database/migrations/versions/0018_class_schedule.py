"""Agenda de aulas por ocorrência. Revision 0018."""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aula_ocorrencia",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=False),
        sa.Column("descricao", sa.Text()),
        sa.Column("estado", sa.String(25), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.CheckConstraint("length(btrim(nome)) > 0", name="ck_aula_nome"),
        sa.CheckConstraint("fim > inicio", name="ck_aula_intervalo"),
        sa.CheckConstraint(
            "estado IN ('AGENDADA', 'CANCELADA')", name="ck_aula_estado"
        ),
        sa.CheckConstraint("revision >= 1", name="ck_aula_revision"),
        schema="academia",
    )
    op.create_index(
        "ix_aula_inicio_id", "aula_ocorrencia", ["inicio", "id"], schema="academia"
    )


def downgrade() -> None:
    op.drop_table("aula_ocorrencia", schema="academia")

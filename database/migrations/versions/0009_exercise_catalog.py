"""Create the exercise catalog and alternative equipment combinations."""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exercicio",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("nome_normalizado", sa.String(120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("grupo_muscular", sa.String(80), nullable=False),
        sa.Column("dispensa_equipamento", sa.Boolean(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.UniqueConstraint("nome_normalizado", name="uq_exercicio_nome_normalizado"),
        sa.CheckConstraint(
            "length(btrim(nome_normalizado)) > 0 AND length(btrim(nome)) > 0 "
            "AND length(btrim(descricao)) > 0 AND length(btrim(grupo_muscular)) > 0",
            name="ck_exercicio_textos",
        ),
        sa.CheckConstraint("revision >= 1", name="ck_exercicio_revisao"),
        schema="academia",
    )
    op.create_table(
        "exercicio_recurso_grupo",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("exercicio_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercicio_id"], ["academia.exercicio.id"], ondelete="CASCADE"
        ),
        schema="academia",
    )
    op.create_index(
        "ix_academia_exercicio_recurso_grupo_exercicio_id",
        "exercicio_recurso_grupo",
        ["exercicio_id"],
        schema="academia",
    )
    op.create_table(
        "exercicio_recurso",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("grupo_id", sa.Uuid(), nullable=False),
        sa.Column("equipamento_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["grupo_id"], ["academia.exercicio_recurso_grupo.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["equipamento_id"], ["academia.equipamento.id"]),
        sa.UniqueConstraint(
            "grupo_id", "equipamento_id", name="uq_exercicio_recurso_grupo"
        ),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("exercicio_recurso", schema="academia")
    op.drop_table("exercicio_recurso_grupo", schema="academia")
    op.drop_table("exercicio", schema="academia")

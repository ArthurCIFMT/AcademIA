"""Store onboarding invitations and scoped sessions by hash."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "convite_onboarding",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("onboarding_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revogado_em", sa.DateTime(timezone=True)),
        sa.Column("consumido_em", sa.DateTime(timezone=True)),
        sa.Column("sessao_restrita_hash", sa.CHAR(64), unique=True),
        sa.Column("sessao_expira_em", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["onboarding_id"], ["academia.onboarding_versao.id"]),
        sa.CheckConstraint(
            "(consumido_em IS NULL AND sessao_restrita_hash IS NULL "
            "AND sessao_expira_em IS NULL) OR "
            "(consumido_em IS NOT NULL AND sessao_restrita_hash IS NOT NULL "
            "AND sessao_expira_em IS NOT NULL AND consumido_em < sessao_expira_em "
            "AND sessao_expira_em <= expira_em)",
            name="ck_convite_onboarding_sessao",
        ),
        schema="academia",
    )
    op.create_index(
        "ix_convite_onboarding_versao_expiracao",
        "convite_onboarding",
        ["onboarding_id", "expira_em"],
        schema="academia",
    )
    op.create_index(
        "uq_convite_onboarding_nao_revogado",
        "convite_onboarding",
        ["onboarding_id"],
        unique=True,
        postgresql_where=sa.text("revogado_em IS NULL"),
        schema="academia",
    )


def downgrade() -> None:
    op.drop_table("convite_onboarding", schema="academia")

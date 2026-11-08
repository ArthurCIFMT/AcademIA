"""Persiste identidade, papéis, perfis, sessões e primeiro acesso."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = "academia"
USER = "academia.usuario.id"


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
        sa.CheckConstraint(
            "email = lower(btrim(email)) AND email !~ '[[:space:]]'",
            name="ck_usuario_email_normalizado",
        ),
        sa.CheckConstraint(
            "estado IN ('CONVIDADO', 'ATIVO', 'INATIVO', 'BLOQUEADO')",
            name="ck_usuario_estado",
        ),
        sa.CheckConstraint(
            "estado <> 'ATIVO' OR senha_hash LIKE '$argon2id$%'",
            name="ck_usuario_credencial_ativa",
        ),
        sa.CheckConstraint("revision >= 1", name="ck_usuario_revision"),
        schema=SCHEMA,
    )
    op.create_table(
        "usuario_papel",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey(USER), nullable=False),
        sa.Column("papel", sa.String(30), nullable=False),
        sa.UniqueConstraint("usuario_id", "papel", name="uq_usuario_papel"),
        sa.CheckConstraint(
            "papel IN ('CLIENTE', 'ADMINISTRADOR', 'ATENDENTE', 'INSTRUTOR')",
            name="ck_usuario_papel",
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "cliente",
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey(USER), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=False),
        sa.Column("telefone", sa.String(25)),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "funcionario",
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey(USER), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("cargo", sa.String(80), nullable=False),
        sa.Column("data_admissao", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "sessao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey(USER), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False),
        sa.Column("csrf_hash", sa.CHAR(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_uso_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revogada_em", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("token_hash", name="uq_sessao_token_hash"),
        sa.CheckConstraint(
            "expira_em > criado_em AND ultimo_uso_em >= criado_em",
            name="ck_sessao_prazos",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_sessao_usuario", "sessao", ["usuario_id"], schema=SCHEMA)
    op.create_table(
        "token_acesso",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey(USER), nullable=False),
        sa.Column("hash", sa.CHAR(64), nullable=False),
        sa.Column("finalidade", sa.String(30), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumido_em", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("hash", name="uq_token_acesso_hash"),
        sa.CheckConstraint(
            "finalidade IN ('PRIMEIRO_ACESSO', 'RECUPERACAO')",
            name="ck_token_acesso_finalidade",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_token_acesso_usuario", "token_acesso", ["usuario_id"], schema=SCHEMA
    )
    op.create_foreign_key(
        "fk_auditoria_ator",
        "auditoria",
        "usuario",
        ["ator_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="RESTRICT",
        postgresql_not_valid=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_auditoria_ator", "auditoria", schema=SCHEMA, type_="foreignkey"
    )
    for table in (
        "token_acesso",
        "sessao",
        "funcionario",
        "cliente",
        "usuario_papel",
        "usuario",
    ):
        op.drop_table(table, schema=SCHEMA)

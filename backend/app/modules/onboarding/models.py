from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OnboardingVersion(Base):
    __tablename__ = "onboarding_versao"
    __table_args__ = (
        UniqueConstraint("cliente_id", "numero", name="uq_onboarding_cliente_numero"),
        UniqueConstraint("cliente_id", "id", name="uq_onboarding_cliente_id"),
        CheckConstraint(
            "numero >= 1 AND revision >= 1 AND schema_version = 1",
            name="ck_onboarding_versoes",
        ),
        CheckConstraint(
            "(estado = 'RASCUNHO' AND idade_snapshot IS NULL AND concluido_em IS NULL "
            "AND concluido_por IS NULL) OR "
            "(estado = 'CONCLUIDO' AND idade_snapshot IS NOT NULL "
            "AND idade_snapshot >= 0 "
            "AND concluido_em IS NOT NULL AND concluido_por IS NOT NULL)",
            name="ck_onboarding_estado",
        ),
        CheckConstraint("jsonb_typeof(dados) = 'object'", name="ck_onboarding_dados"),
        Index(
            "uq_onboarding_cliente_rascunho",
            "cliente_id",
            unique=True,
            postgresql_where=text("estado = 'RASCUNHO'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    numero: Mapped[int]
    estado: Mapped[str] = mapped_column(String(20))
    schema_version: Mapped[int]
    idade_snapshot: Mapped[int | None]
    dados: Mapped[dict[str, object]] = mapped_column(JSONB)
    criado_por: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    concluido_por: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.usuario.id")
    )
    revision: Mapped[int]


class OnboardingInvitation(Base):
    __tablename__ = "convite_onboarding"
    __table_args__ = (
        CheckConstraint(
            "(consumido_em IS NULL AND sessao_restrita_hash IS NULL "
            "AND sessao_expira_em IS NULL) OR "
            "(consumido_em IS NOT NULL AND sessao_restrita_hash IS NOT NULL "
            "AND sessao_expira_em IS NOT NULL AND consumido_em < sessao_expira_em "
            "AND sessao_expira_em <= expira_em)",
            name="ck_convite_onboarding_sessao",
        ),
        Index("ix_convite_onboarding_versao_expiracao", "onboarding_id", "expira_em"),
        Index(
            "uq_convite_onboarding_nao_revogado",
            "onboarding_id",
            unique=True,
            postgresql_where=text("revogado_em IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    onboarding_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.onboarding_versao.id")
    )
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sessao_restrita_hash: Mapped[str | None] = mapped_column(CHAR(64), unique=True)
    sessao_expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Evaluation(Base):
    __tablename__ = "avaliacao"
    __table_args__ = (
        ForeignKeyConstraint(
            ["cliente_id", "onboarding_id"],
            ["academia.onboarding_versao.cliente_id", "academia.onboarding_versao.id"],
            name="fk_avaliacao_onboarding_cliente",
        ),
        CheckConstraint("jsonb_typeof(dados) = 'object'", name="ck_avaliacao_dados"),
        Index("ix_avaliacao_cliente_registro", "cliente_id", "registrado_em", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    instrutor_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    onboarding_id: Mapped[UUID]
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dados: Mapped[dict[str, object]] = mapped_column(JSONB)

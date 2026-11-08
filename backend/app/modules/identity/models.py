from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AccountState(StrEnum):
    CONVIDADO = "CONVIDADO"
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    BLOQUEADO = "BLOQUEADO"


class Role(StrEnum):
    CLIENTE = "CLIENTE"
    ADMINISTRADOR = "ADMINISTRADOR"
    ATENDENTE = "ATENDENTE"
    INSTRUTOR = "INSTRUTOR"


class User(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuario_email"),
        CheckConstraint(
            "email = lower(btrim(email)) AND email !~ '[[:space:]]'",
            name="ck_usuario_email_normalizado",
        ),
        CheckConstraint(
            "estado IN ('CONVIDADO', 'ATIVO', 'INATIVO', 'BLOQUEADO')",
            name="ck_usuario_estado",
        ),
        CheckConstraint(
            "estado <> 'ATIVO' OR senha_hash LIKE '$argon2id$%'",
            name="ck_usuario_credencial_ativa",
        ),
        CheckConstraint("revision >= 1", name="ck_usuario_revision"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    senha_hash: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int]


class UserRole(Base):
    __tablename__ = "usuario_papel"
    __table_args__ = (
        UniqueConstraint("usuario_id", "papel", name="uq_usuario_papel"),
        CheckConstraint(
            "papel IN ('CLIENTE', 'ADMINISTRADOR', 'ATENDENTE', 'INSTRUTOR')",
            name="ck_usuario_papel",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    papel: Mapped[str] = mapped_column(String(30))


class StoredSession(Base):
    __tablename__ = "sessao"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_sessao_token_hash"),
        Index("ix_sessao_usuario", "usuario_id"),
        CheckConstraint(
            "expira_em > criado_em AND ultimo_uso_em >= criado_em",
            name="ck_sessao_prazos",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    token_hash: Mapped[str] = mapped_column(CHAR(64))
    csrf_hash: Mapped[str] = mapped_column(CHAR(64))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ultimo_uso_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccessToken(Base):
    __tablename__ = "token_acesso"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_token_acesso_hash"),
        Index("ix_token_acesso_usuario", "usuario_id"),
        CheckConstraint(
            "finalidade IN ('PRIMEIRO_ACESSO', 'RECUPERACAO')",
            name="ck_token_acesso_finalidade",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    hash: Mapped[str] = mapped_column(CHAR(64))
    finalidade: Mapped[str] = mapped_column(String(30))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

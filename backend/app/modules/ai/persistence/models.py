from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Execution(Base):
    __tablename__ = "execucao_ia"
    __table_args__ = (
        UniqueConstraint("cliente_id", "idempotency_key", name="uq_execucao_ia_chave"),
        ForeignKeyConstraint(
            ["cliente_id", "onboarding_id"],
            ["academia.onboarding_versao.cliente_id", "academia.onboarding_versao.id"],
        ),
        ForeignKeyConstraint(
            ["cliente_id", "versao_publicada_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
        ),
        ForeignKeyConstraint(
            ["cliente_id", "versao_base_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
        ),
        CheckConstraint(
            "finalidade IN ('DUVIDA','GERACAO','ADAPTACAO')",
            name="ck_execucao_finalidade",
        ),
        CheckConstraint(
            "(estado = 'EM_EXECUCAO') = (terminada_em IS NULL) "
            "AND prazo_em > iniciada_em",
            name="ck_execucao_prazo",
        ),
        CheckConstraint(
            "jsonb_typeof(resultado) = 'object' AND NOT (resultado ? 'proposta')",
            name="ck_execucao_sem_copia_ficha",
        ),
        Index("ix_execucao_cliente_tempo", "cliente_id", "iniciada_em"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    ator_id: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    entrada_hash: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))
    finalidade: Mapped[str] = mapped_column(String(25))
    estado: Mapped[str] = mapped_column(String(35))
    onboarding_id: Mapped[UUID | None]
    versao_base_id: Mapped[UUID | None]
    versao_publicada_id: Mapped[UUID | None]
    worker_id: Mapped[UUID]
    config_version: Mapped[int]
    modelo: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(60))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prazo_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terminada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resultado: Mapped[dict[str, object]] = mapped_column(JSONB)


class TriageRecord(Base):
    __tablename__ = "triagem"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    execucao_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.execucao_ia.id"), unique=True
    )
    onboarding_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.onboarding_versao.id")
    )
    resumo: Mapped[dict[str, object]] = mapped_column(JSONB)
    regra_version: Mapped[int]
    estado: Mapped[str | None] = mapped_column(String(35))
    motivos: Mapped[list[str]] = mapped_column(JSONB)


class StageRecord(Base):
    __tablename__ = "etapa_ia"
    __table_args__ = (
        UniqueConstraint("execucao_id", "tipo", name="uq_etapa_execucao_tipo"),
        CheckConstraint(
            "chamadas BETWEEN 0 AND 1 AND limite_saida_tokens > 0 AND prompt_bytes > 0",
            name="ck_etapa_orcamento",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    execucao_id: Mapped[UUID] = mapped_column(ForeignKey("academia.execucao_ia.id"))
    tipo: Mapped[str] = mapped_column(String(25))
    estado: Mapped[str] = mapped_column(String(25))
    chamadas: Mapped[int]
    limite_saida_tokens: Mapped[int]
    prompt_bytes: Mapped[int]
    prompt_sha256: Mapped[str] = mapped_column(String(64))
    enviada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracao_ms: Mapped[int | None]
    tokens_entrada: Mapped[int | None]
    tokens_saida: Mapped[int | None]
    dados: Mapped[dict[str, object]] = mapped_column(JSONB)


class EvidenceRecord(Base):
    __tablename__ = "evidencia_execucao"
    __table_args__ = (
        UniqueConstraint(
            "execucao_id", "fragmento_id", name="uq_evidencia_execucao_fragmento"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    execucao_id: Mapped[UUID] = mapped_column(ForeignKey("academia.execucao_ia.id"))
    fragmento_id: Mapped[UUID] = mapped_column(ForeignKey("academia.fragmento.id"))
    finalidade: Mapped[str] = mapped_column(String(25))
    metadados: Mapped[dict[str, object]] = mapped_column(JSONB)

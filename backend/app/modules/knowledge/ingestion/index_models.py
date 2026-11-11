from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Ingestion(Base):
    __tablename__ = "ingestao"
    __table_args__ = (
        UniqueConstraint(
            "documento_versao_id", "config_hash", name="uq_ingestao_config"
        ),
        CheckConstraint(
            "estado IN "
            "('PROCESSANDO','FALHA','CONCLUIDA','PENDENTE_TRATAMENTO','REVOGADA') "
            "AND total >= 0 AND revision >= 1",
            name="ck_ingestao_estado",
        ),
        CheckConstraint(
            "(estado = 'CONCLUIDA' AND concluida_em IS NOT NULL AND erro_codigo IS "
            "NULL AND total > 0) OR (estado <> 'CONCLUIDA' AND concluida_em IS NULL)",
            name="ck_ingestao_conclusao",
        ),
        Index("ix_ingestao_disponivel", "estado", "colecao"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    documento_versao_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.documento_versao.id")
    )
    aprovacao_revisao: Mapped[int]
    extracao_id: Mapped[UUID]
    config_hash: Mapped[str] = mapped_column(String(64))
    configuracao: Mapped[dict[str, object]] = mapped_column(JSONB)
    plano_hash: Mapped[str] = mapped_column(String(64))
    colecao: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(25))
    total: Mapped[int]
    erro_codigo: Mapped[str | None] = mapped_column(String(80))
    criado_por: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int]


class Fragment(Base):
    __tablename__ = "fragmento"
    __table_args__ = (
        UniqueConstraint("ingestao_id", "ordem", name="uq_fragmento_ordem"),
        UniqueConstraint("vetor_id", name="uq_fragmento_vetor"),
        CheckConstraint(
            "ordem >= 1 AND inicio >= 0 AND fim > inicio AND tokens >= 1 AND tokens "
            "<= 300 AND input_tokens <= 512",
            name="ck_fragmento_limites",
        ),
        CheckConstraint(
            "(pagina_inicio IS NULL AND pagina_fim IS NULL AND linha_inicio IS NOT "
            "NULL AND linha_fim IS NOT NULL AND linha_inicio >= 1 AND linha_fim >= "
            "linha_inicio) OR (pagina_inicio IS NOT NULL AND pagina_fim IS NOT NULL "
            "AND pagina_inicio >= 1 AND pagina_fim = pagina_inicio AND linha_inicio "
            "IS NULL AND linha_fim IS NULL)",
            name="ck_fragmento_origem",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    ingestao_id: Mapped[UUID] = mapped_column(ForeignKey("academia.ingestao.id"))
    ordem: Mapped[int]
    pagina_inicio: Mapped[int | None]
    pagina_fim: Mapped[int | None]
    linha_inicio: Mapped[int | None]
    linha_fim: Mapped[int | None]
    secao: Mapped[str | None] = mapped_column(Text)
    inicio: Mapped[int]
    fim: Mapped[int]
    texto_hash: Mapped[str] = mapped_column(String(64))
    tokens: Mapped[int]
    input_tokens: Mapped[int]
    vetor_id: Mapped[UUID]
    colecao: Mapped[str] = mapped_column(String(100))
    indexado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

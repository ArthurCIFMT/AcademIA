from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Document(Base):
    __tablename__ = "documento"
    __table_args__ = (
        UniqueConstraint("ambiente", "catalogo_id", name="uq_documento_catalogo"),
        UniqueConstraint("id", "ambiente", name="uq_documento_ambiente"),
        CheckConstraint(
            "ambiente IN ('LITERATURA','TESTE')", name="ck_documento_ambiente"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    ambiente: Mapped[str] = mapped_column(String(15))
    catalogo_id: Mapped[str] = mapped_column(String(40))
    titulo: Mapped[str] = mapped_column(Text)
    origem_url: Mapped[str] = mapped_column(Text)
    licenca: Mapped[str] = mapped_column(Text)


class DocumentVersion(Base):
    __tablename__ = "documento_versao"
    __table_args__ = (
        ForeignKeyConstraint(
            ["documento_id", "ambiente"],
            ["academia.documento.id", "academia.documento.ambiente"],
            name="fk_documento_versao_ambiente",
        ),
        UniqueConstraint("documento_id", "numero", name="uq_documento_numero"),
        UniqueConstraint("ambiente", "sha256", name="uq_documento_hash"),
        CheckConstraint(
            "numero >= 1 AND revision >= 1 AND tamanho_bytes > 0 AND formato IN "
            "('PDF','TXT') AND jsonb_typeof(metadados) = 'object'",
            name="ck_documento_conteudo",
        ),
        CheckConstraint(
            "estado IN ('PENDENTE','APROVADO','REVOGADO') AND "
            "((estado = 'PENDENTE' AND aprovado_por IS NULL AND aprovado_em IS NULL) "
            "OR "
            "(estado <> 'PENDENTE' AND aprovado_por IS NOT NULL AND aprovado_em IS "
            "NOT NULL)) AND "
            "((estado = 'REVOGADO' AND revogado_por IS NOT NULL AND revogado_em IS "
            "NOT NULL AND motivo_revogacao IS NOT NULL AND "
            "length(btrim(motivo_revogacao)) > 0) OR "
            "(estado <> 'REVOGADO' AND revogado_por IS NULL AND revogado_em IS NULL "
            "AND motivo_revogacao IS NULL))",
            name="ck_documento_aprovacao",
        ),
        Index("ix_documento_uso", "ambiente", "estado"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    documento_id: Mapped[UUID]
    ambiente: Mapped[str] = mapped_column(String(15))
    numero: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    idioma: Mapped[str] = mapped_column(String(12))
    arquivo_ref: Mapped[str] = mapped_column(Text)
    formato: Mapped[str] = mapped_column(String(3))
    tamanho_bytes: Mapped[int]
    metadados: Mapped[dict[str, object]] = mapped_column(JSONB)
    criado_por: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(25))
    aprovado_por: Mapped[UUID | None] = mapped_column(ForeignKey("academia.usuario.id"))
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogado_por: Mapped[UUID | None] = mapped_column(ForeignKey("academia.usuario.id"))
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_revogacao: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int]

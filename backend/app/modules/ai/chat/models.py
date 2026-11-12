from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Conversation(Base):
    __tablename__ = "conversa"
    id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.cliente.usuario_id"), primary_key=True
    )


class Message(Base):
    __tablename__ = "mensagem"
    __table_args__ = (
        UniqueConstraint("conversa_id", "solicitacao_id", name="uq_mensagem_pedido"),
        CheckConstraint(
            "length(btrim(pergunta)) BETWEEN 1 AND 1000 "
            "AND jsonb_typeof(pedido) = 'object'",
            name="ck_mensagem_pergunta",
        ),
        ForeignKeyConstraint(
            ["conversa_id", "versao_contexto_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
            name="fk_mensagem_ficha_contexto",
        ),
        Index("ix_mensagem_historico", "conversa_id", "criada_em"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    conversa_id: Mapped[UUID] = mapped_column(ForeignKey("academia.conversa.id"))
    solicitacao_id: Mapped[UUID]
    pergunta: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(Text)
    erro_codigo: Mapped[str | None] = mapped_column(Text)
    pedido: Mapped[dict[str, object]] = mapped_column(JSONB)
    versao_contexto_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.versao_ficha.id")
    )
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

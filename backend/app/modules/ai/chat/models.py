from datetime import datetime
from typing import cast
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


class Message(Base):
    __tablename__ = "mensagem"
    __table_args__ = (
        UniqueConstraint("cliente_id", "solicitacao_id", name="uq_mensagem_pedido"),
        CheckConstraint(
            "jsonb_typeof(pedido) = 'object' AND pedido ? 'mensagem' "
            "AND jsonb_typeof(pedido->'mensagem') = 'string' "
            "AND length(btrim(pedido->>'mensagem')) BETWEEN 1 AND 1000",
            name="ck_mensagem_pergunta",
        ),
        ForeignKeyConstraint(
            ["cliente_id", "versao_contexto_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
            name="fk_mensagem_ficha_contexto",
        ),
        Index("ix_mensagem_historico", "cliente_id", "criada_em"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.cliente.usuario_id", name="fk_mensagem_cliente")
    )
    solicitacao_id: Mapped[UUID]
    estado: Mapped[str] = mapped_column(Text)
    erro_codigo: Mapped[str | None] = mapped_column(Text)
    pedido: Mapped[dict[str, object]] = mapped_column(JSONB)
    versao_contexto_id: Mapped[UUID | None]
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @property
    def pergunta(self) -> str:
        return cast(str, self.pedido["mensagem"])

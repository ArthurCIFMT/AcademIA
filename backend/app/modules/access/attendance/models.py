from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Presence(Base):
    __tablename__ = "presenca"
    __table_args__ = (
        CheckConstraint(
            "id = entrada_evento_id AND entrada_evento_id <> saida_evento_id",
            name="ck_presenca_eventos",
        ),
        Index(
            "uq_presenca_cliente_aberta",
            "cliente_id",
            unique=True,
            postgresql_where=text("saida_evento_id IS NULL"),
        ),
        Index("ix_presenca_cliente", "cliente_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    entrada_evento_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), unique=True
    )
    saida_evento_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), unique=True
    )

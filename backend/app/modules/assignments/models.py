from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Assignment(Base):
    __tablename__ = "designacao"
    __table_args__ = (
        CheckConstraint("fim IS NULL OR fim >= inicio", name="ck_designacao_periodo"),
        Index(
            "uq_designacao_cliente_vigente",
            "cliente_id",
            unique=True,
            postgresql_where=text("fim IS NULL"),
        ),
        Index(
            "ix_designacao_instrutor_vigente",
            "instrutor_id",
            "cliente_id",
            postgresql_where=text("fim IS NULL"),
        ),
        Index("ix_designacao_cliente_inicio", "cliente_id", "inicio", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    instrutor_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    atribuido_por: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditRecord(Base):
    __tablename__ = "auditoria"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    ator_id: Mapped[UUID | None]
    acao: Mapped[str] = mapped_column(String(80))
    recurso_tipo: Mapped[str] = mapped_column(String(60))
    recurso_id: Mapped[UUID | None]
    motivo: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[UUID]
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

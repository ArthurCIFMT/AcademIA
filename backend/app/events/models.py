from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OutboxRecord(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        CheckConstraint("schema_version > 0", name="ck_outbox_schema_version"),
        CheckConstraint(
            "(estado = 'PENDENTE' AND entregue_em IS NULL) OR "
            "(estado = 'ENTREGUE' AND entregue_em IS NOT NULL)",
            name="ck_outbox_entrega",
        ),
        Index(
            "ix_outbox_pendentes",
            "criado_em",
            "id",
            postgresql_where=text("estado = 'PENDENTE'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_tipo: Mapped[str] = mapped_column(String(80))
    schema_version: Mapped[int]
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
    estado: Mapped[str] = mapped_column(String(25))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FacialReference(Base):
    __tablename__ = "biometria"
    __table_args__ = (
        CheckConstraint(
            "(estado = 'PREPARANDO' AND image_id IS NULL) OR "
            "(estado IN ('PRONTA', 'ATIVA') AND image_id IS NOT NULL)",
            name="ck_biometria_referencia",
        ),
        Index(
            "uq_biometria_ativa_cliente",
            "cliente_id",
            unique=True,
            postgresql_where=text("estado = 'ATIVA'"),
        ),
        Index(
            "uq_biometria_pendente_cliente",
            "cliente_id",
            unique=True,
            postgresql_where=text("estado IN ('PREPARANDO', 'PRONTA')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    subject_externo: Mapped[str] = mapped_column(String(120), unique=True)
    image_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    estado: Mapped[str] = mapped_column(String(25))
    cadastrada_por: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

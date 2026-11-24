from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ManualIdentification(Base):
    __tablename__ = "identificacao_manual"
    __table_args__ = (
        CheckConstraint("btrim(motivo) <> ''", name="ck_identificacao_manual_motivo"),
        CheckConstraint(
            "evento_id <> evento_falha_id", name="ck_identificacao_manual_eventos"
        ),
    )

    evento_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), primary_key=True
    )
    evento_falha_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), unique=True
    )
    atendente_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    motivo: Mapped[str] = mapped_column(String(240))

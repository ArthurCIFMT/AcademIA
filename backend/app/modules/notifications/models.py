from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NoticeKind(StrEnum):
    TREINO_PARA_AVALIAR = "TREINO_PARA_AVALIAR"
    ALTERACAO_CRITICA = "ALTERACAO_CRITICA"


class EmailKind(StrEnum):
    PRIMEIRO_ACESSO = "PRIMEIRO_ACESSO"
    RECUPERACAO = "RECUPERACAO"
    CONVITE_ONBOARDING = "CONVITE_ONBOARDING"
    TREINO_PARA_AVALIAR = "TREINO_PARA_AVALIAR"
    ALTERACAO_CRITICA = "ALTERACAO_CRITICA"


class DeliveryState(StrEnum):
    ENVIANDO = "ENVIANDO"
    ENVIADO = "ENVIADO"
    FALHOU = "FALHOU"
    INCERTO = "INCERTO"


class Notification(Base):
    __tablename__ = "notificacao"
    __table_args__ = (
        UniqueConstraint(
            "destinatario_id",
            "evento_id",
            "canal",
            name="uq_notificacao_dest_evento_canal",
        ),
        CheckConstraint(
            "(canal = 'INTERNO' AND estado = 'PENDENTE' AND tentativas = 0 "
            "AND tipo IN ('TREINO_PARA_AVALIAR', 'ALTERACAO_CRITICA')) OR "
            "(canal = 'EMAIL' AND estado IN "
            "('ENVIANDO', 'ENVIADO', 'FALHOU', 'INCERTO') "
            "AND tentativas BETWEEN 1 AND 3 AND lida_em IS NULL "
            "AND tipo IN ('PRIMEIRO_ACESSO', 'RECUPERACAO', 'CONVITE_ONBOARDING', "
            "'TREINO_PARA_AVALIAR', 'ALTERACAO_CRITICA'))",
            name="ck_notificacao_fluxo",
        ),
        Index("ix_notificacao_lista", "destinatario_id", "canal", "criada_em", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    destinatario_id: Mapped[UUID] = mapped_column(ForeignKey("academia.usuario.id"))
    evento_id: Mapped[UUID]
    canal: Mapped[str] = mapped_column(String(25))
    tipo: Mapped[str] = mapped_column(String(25))
    estado: Mapped[str] = mapped_column(String(25))
    tentativas: Mapped[int]
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    atualizada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

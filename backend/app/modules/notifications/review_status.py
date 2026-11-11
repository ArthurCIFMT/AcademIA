"""Consulta interna ao aviso existente; não cria nem tenta envio."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.email import DeliveryResult
from app.modules.notifications.models import DeliveryState, Notification


@dataclass(frozen=True)
class ReviewNoticeStatus:
    internal_registered: bool
    email: DeliveryResult | None


def review_notice_status(
    session: Session, event: UUID, recipient: UUID
) -> ReviewNoticeStatus:
    records = list(
        session.scalars(
            select(Notification).where(
                Notification.evento_id == event,
                Notification.destinatario_id == recipient,
                Notification.tipo == "TREINO_PARA_AVALIAR",
            )
        )
    )
    internal = any(row.canal == "INTERNO" for row in records)
    email = next((row for row in records if row.canal == "EMAIL"), None)
    return ReviewNoticeStatus(
        internal,
        DeliveryResult(DeliveryState(email.estado), email.tentativas)
        if email
        else None,
    )

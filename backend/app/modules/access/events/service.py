from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.access.biometrics.images import MAX_IMAGE_BYTES, clean_face_image
from app.modules.access.biometrics.provider import (
    FaceCandidate,
    FacialProvider,
    FacialProviderError,
    RejectedFace,
)
from app.modules.access.biometrics.service import active_client_for_subject
from app.modules.access.events.contracts import (
    CaptureRequest,
    Direction,
    ExternalIdentification,
    IdentificationReceipt,
    IdentificationStatus,
    Origin,
)
from app.modules.access.events.models import AccessEvent


class IdentificationConflict(Exception):
    """A origem já usou o identificador com dados diferentes."""


@dataclass(frozen=True)
class Identification:
    status: IdentificationStatus
    client_id: UUID | None = None
    similarity: float | None = None


def classify(
    candidates: Sequence[FaceCandidate],
    threshold: float,
    resolve: Callable[[str], UUID | None],
) -> Identification:
    if not candidates:
        return Identification("DESCONHECIDO")
    best = max(candidates, key=lambda candidate: candidate.similarity)
    if best.similarity < threshold:
        return Identification("PONTUACAO_BAIXA", similarity=best.similarity)
    positive = {
        candidate.subject
        for candidate in candidates
        if candidate.similarity >= threshold
    }
    if len(positive) > 1:
        return Identification("AMBIGUO", similarity=best.similarity)
    client_id = resolve(best.subject)
    if client_id is None:
        return Identification("DESCONHECIDO", similarity=best.similarity)
    return Identification("IDENTIFICADO", client_id, best.similarity)


@dataclass(frozen=True)
class EventRequest:
    origin: Origin
    event_id: UUID
    direction: Direction
    occurred_at: datetime
    fingerprint: str

    @classmethod
    def capture(cls, data: CaptureRequest, actor_id: UUID) -> EventRequest:
        fingerprint = sha256(
            f"{actor_id}:{data.model_dump_json()}".encode()
        ).hexdigest()
        return cls(
            "ACADEMIA", data.evento_id, data.direcao, datetime.now(UTC), fingerprint
        )

    @classmethod
    def external(cls, data: ExternalIdentification) -> EventRequest:
        fingerprint = sha256(data.model_dump_json().encode()).hexdigest()
        return cls(
            "INTEGRACAO_FACIAL",
            data.evento_id,
            data.direcao,
            data.ocorrido_em,
            fingerprint,
        )


def receive(
    db: Session, event: EventRequest, identify: Callable[[], Identification]
) -> tuple[IdentificationReceipt, bool]:
    # Um replay concorrente aguarda o primeiro commit antes de consultar o provedor.
    lock_key = f"evento_acesso:{event.origin}:{event.event_id}"
    db.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(lock_key, 0))))
    existing = db.scalar(
        select(AccessEvent).where(
            AccessEvent.origem == event.origin,
            AccessEvent.event_id_externo == str(event.event_id),
        )
    )
    if existing is not None:
        if (
            existing.payload_hash != event.fingerprint
            or existing.tipo != "IDENTIFICACAO"
        ):
            raise IdentificationConflict
        return _receipt(existing), False

    result = identify()
    row = AccessEvent(
        id=uuid4(),
        origem=event.origin,
        event_id_externo=str(event.event_id),
        tipo="IDENTIFICACAO",
        cliente_id=result.client_id,
        direcao=event.direction,
        ocorrido_em=event.occurred_at,
        payload_hash=event.fingerprint,
        resultado_identificacao=result.status,
        similaridade=result.similarity,
    )
    db.add(row)
    db.flush()
    return _receipt(row), True


def _receipt(row: AccessEvent) -> IdentificationReceipt:
    return IdentificationReceipt.model_validate(
        dict(
            id=row.id,
            evento_id=row.event_id_externo,
            origem=row.origem,
            ocorrido_em=row.ocorrido_em,
            direcao=row.direcao,
            resultado=row.resultado_identificacao,
            similaridade=row.similaridade,
            cliente_id=row.cliente_id,
        )
    )


def from_capture(
    db: Session, data: CaptureRequest, provider: FacialProvider | None, threshold: float
) -> Identification:
    image = clean_face_image(
        data.imagem_base64,
        max_bytes=provider.max_image_bytes if provider else MAX_IMAGE_BYTES,
    )
    if provider is None:
        return Identification("FALHA_PROVEDOR")
    try:
        candidates = provider.recognize(image)
    except RejectedFace:
        return Identification("CAPTURA_INVALIDA")
    except FacialProviderError:
        return Identification("FALHA_PROVEDOR")
    return classify(
        candidates, threshold, lambda subject: active_client_for_subject(db, subject)
    )


def from_source(
    db: Session, data: ExternalIdentification, threshold: float
) -> Identification:
    if data.resultado != "CORRESPONDENCIA":
        return Identification(data.resultado)
    assert data.subject is not None and data.similaridade is not None
    candidates = [
        FaceCandidate(subject=str(data.subject), similarity=data.similaridade)
    ]
    return classify(
        candidates, threshold, lambda subject: active_client_for_subject(db, subject)
    )

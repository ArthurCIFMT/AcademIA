from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.events.contracts import AuditEvent
from app.modules.access.biometrics.images import clean_face_image
from app.modules.access.biometrics.models import FacialReference
from app.modules.access.biometrics.provider import FacialProvider, FacialProviderError
from app.modules.audit.service import record_audit
from app.modules.memberships.service import has_registered_membership
from app.modules.notifications.service import notify_critical_change
from app.modules.people.membership_directory import MembershipDirectory


class BiometricsError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class ReferenceStatus(BaseModel):
    cadastrada: bool
    elegivel: bool
    disponivel: bool
    atualizada_em: UtcTimestamp | None
    pendencia: Literal["ENVIO", "TROCA"] | None


def _references(
    db: Session, client_id: UUID
) -> tuple[FacialReference | None, FacialReference | None]:
    rows = db.scalars(
        select(FacialReference).where(FacialReference.cliente_id == client_id)
    ).all()
    return (
        next((ref for ref in rows if ref.estado == "ATIVA"), None),
        next((ref for ref in rows if ref.estado != "ATIVA"), None),
    )


def active_client_for_subject(db: Session, subject: str) -> UUID | None:
    """Resolve apenas sujeitos com referência confirmada pelo MOD-07."""
    return db.scalar(
        select(FacialReference.cliente_id).where(
            FacialReference.subject_externo == subject,
            FacialReference.estado == "ATIVA",
        )
    )


def _audit(
    db: Session,
    actor_id: UUID,
    reference_id: UUID,
    correlation: UUID,
    action: str,
    reason: str | None = None,
) -> UUID:
    event = AuditEvent(
        id=uuid4(),
        actor_id=actor_id,
        action=action,
        resource_type="biometria",
        resource_id=reference_id,
        reason_code=reason,
        correlation_id=correlation,
        occurred_at=datetime.now(UTC),
    )
    record_audit(db, event)
    return event.id


def _eligible(db: Session, directory: MembershipDirectory, client_id: UUID) -> bool:
    return directory.client_is_eligible(client_id) and has_registered_membership(
        db, client_id
    )


def status(db: Session, client_id: UUID, *, available: bool) -> ReferenceStatus:
    directory = MembershipDirectory(db)
    if not directory.client_exists(client_id):
        raise BiometricsError(404)
    active, pending = _references(db, client_id)
    return ReferenceStatus(
        cadastrada=active is not None,
        elegivel=_eligible(db, directory, client_id),
        disponivel=available,
        atualizada_em=active.criada_em if active else None,
        pendencia=("TROCA" if pending.estado == "PRONTA" else "ENVIO")
        if pending
        else None,
    )


def _require_write(db: Session, client_id: UUID, actor_id: UUID) -> None:
    directory = MembershipDirectory(db)
    directory.lock_people(client_id, actor_id)
    if not directory.attendant_is_active(actor_id):
        raise BiometricsError(403)
    if not directory.client_exists(client_id):
        raise BiometricsError(404)
    if not _eligible(db, directory, client_id):
        raise BiometricsError(409)


class ReferenceService:
    def __init__(
        self, sessions: sessionmaker[Session], provider: FacialProvider
    ) -> None:
        self._sessions = sessions
        self._provider = provider

    def register(
        self, client_id: UUID, actor_id: UUID, correlation: UUID, encoded: str
    ) -> ReferenceStatus:
        image = clean_face_image(encoded, max_bytes=self._provider.max_image_bytes)
        reference_id = uuid4()
        step = "deteccao"
        try:
            self._reserve(client_id, actor_id, reference_id, image)
            step = "cadastro_externo"
            with self._sessions.begin() as db:
                _require_write(db, client_id, actor_id)
                pending = db.get(FacialReference, reference_id)
                if pending is None or pending.estado != "PREPARANDO":
                    raise BiometricsError(409)
                pending.image_id = str(
                    self._provider.add_example(pending.subject_externo, image)
                )
                pending.estado = "PRONTA"
            step = "descarte_anterior"
            with self._sessions.begin() as db:
                _require_write(db, client_id, actor_id)
                active, pending = _references(db, client_id)
                if active is not None and active.id == reference_id:
                    return status(db, client_id, available=True)
                if pending is None or pending.id != reference_id:
                    raise BiometricsError(409)
                self._activate(db, active, pending, actor_id, correlation)
                return status(db, client_id, available=True)
        except FacialProviderError:
            self._record_failure(actor_id, reference_id, correlation, step)
            raise BiometricsError(503) from None

    def _reserve(
        self, client_id: UUID, actor_id: UUID, reference_id: UUID, image: bytes
    ) -> None:
        with self._sessions.begin() as db:
            _require_write(db, client_id, actor_id)
            if _references(db, client_id)[1] is not None:
                raise BiometricsError(409)
            self._provider.validate_photo(image)
            db.add(
                FacialReference(
                    id=reference_id,
                    cliente_id=client_id,
                    subject_externo=str(uuid4()),
                    estado="PREPARANDO",
                    cadastrada_por=actor_id,
                    criada_em=datetime.now(UTC),
                )
            )

    def resume(
        self, client_id: UUID, actor_id: UUID, correlation: UUID
    ) -> ReferenceStatus:
        reference_id = client_id
        try:
            with self._sessions.begin() as db:
                _require_write(db, client_id, actor_id)
                active, pending = _references(db, client_id)
                if pending is None:
                    return status(db, client_id, available=True)
                reference_id = pending.id
                examples = self._provider.list_examples(pending.subject_externo)
                if not examples:
                    db.delete(pending)
                    db.flush()
                    _audit(
                        db,
                        actor_id,
                        pending.id,
                        correlation,
                        "biometria.envio_encerrado",
                    )
                    return status(db, client_id, available=True)
                if len(examples) != 1 or (
                    pending.image_id is not None
                    and str(examples[0]) != pending.image_id
                ):
                    raise FacialProviderError
                # Persiste o ID recém-confirmado antes de poder remover o anterior.
                pending.image_id = str(examples[0])
                pending.estado = "PRONTA"

            with self._sessions.begin() as db:
                _require_write(db, client_id, actor_id)
                active, pending = _references(db, client_id)
                if pending is not None and pending.id == reference_id:
                    self._activate(db, active, pending, actor_id, correlation)
                return status(db, client_id, available=True)
        except FacialProviderError:
            self._record_failure(actor_id, reference_id, correlation, "recuperacao")
            raise BiometricsError(503) from None

    def _activate(
        self,
        db: Session,
        active: FacialReference | None,
        pending: FacialReference,
        actor_id: UUID,
        correlation: UUID,
    ) -> None:
        if active is not None:
            assert active.image_id is not None
            self._provider.delete_example(active.subject_externo, UUID(active.image_id))
            db.delete(active)
            db.flush()
        pending.estado = "ATIVA"
        pending.criada_em = datetime.now(UTC)
        db.flush()
        action = "biometria.cadastrada" if active is None else "biometria.substituida"
        event = _audit(db, actor_id, pending.id, correlation, action)
        notify_critical_change(db, event)

    def _record_failure(
        self, actor_id: UUID, reference_id: UUID, correlation: UUID, step: str
    ) -> None:
        with self._sessions.begin() as db:
            _audit(
                db, actor_id, reference_id, correlation, "biometria.falha_externa", step
            )

from datetime import date, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import ScalarSelect

from app.modules.identity.service import utc_now
from app.modules.onboarding.models import Evaluation, OnboardingVersion
from app.modules.onboarding.schemas import (
    Completion,
    ConfirmUpdate,
    DraftChange,
    DraftData,
    DraftView,
    OnboardingData,
    OwnOnboarding,
    SnapshotView,
)
from app.modules.people.onboarding_directory import lock_onboarding_client

DRAFT = "RASCUNHO"
COMPLETED = "CONCLUIDO"
_ACADEMY_ZONE = ZoneInfo("America/Sao_Paulo")


class OnboardingError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _latest_completed_id(client_id: UUID) -> ScalarSelect[UUID]:
    return (
        select(OnboardingVersion.id)
        .where(
            OnboardingVersion.cliente_id == client_id,
            OnboardingVersion.estado == COMPLETED,
        )
        .order_by(OnboardingVersion.numero.desc())
        .limit(1)
        .correlate(None)
        .scalar_subquery()
    )


def _versions(
    session: Session, client_id: UUID
) -> tuple[OnboardingVersion | None, OnboardingVersion | None]:
    rows = session.scalars(
        select(OnboardingVersion).where(
            OnboardingVersion.cliente_id == client_id,
            or_(
                OnboardingVersion.estado == DRAFT,
                OnboardingVersion.id == _latest_completed_id(client_id),
            ),
        )
    )
    draft, completed = None, None
    for row in rows:
        if row.estado == DRAFT:
            draft = row
        else:
            completed = row
    return draft, completed


def draft_view(row: OnboardingVersion) -> DraftView:
    return DraftView(
        id=row.id,
        numero=row.numero,
        revisao=row.revision,
        criado_por=row.criado_por,
        estado=DRAFT,
        schema_version=1,
        dados=DraftData.model_validate(row.dados),
    )


def _snapshot(row: OnboardingVersion) -> SnapshotView:
    if (
        row.idade_snapshot is None
        or row.concluido_em is None
        or row.concluido_por is None
    ):
        raise RuntimeError("Metadados de conclusão ausentes.")
    return SnapshotView(
        id=row.id,
        numero=row.numero,
        revisao=row.revision,
        criado_por=row.criado_por,
        estado=COMPLETED,
        schema_version=1,
        dados=OnboardingData.model_validate(row.dados),
        idade_snapshot=row.idade_snapshot,
        concluido_em=row.concluido_em,
        concluido_por=row.concluido_por,
    )


def get_own(session: Session, client_id: UUID) -> OwnOnboarding:
    draft, completed = _versions(session, client_id)
    return OwnOnboarding(
        rascunho=draft_view(draft) if draft else None,
        concluido=_snapshot(completed) if completed else None,
    )


def get_snapshot(
    session: Session, client_id: UUID, snapshot_id: UUID
) -> SnapshotView | None:
    """Lê uma versão concluída dentro do escopo do cliente já autorizado."""
    row = session.scalar(
        select(OnboardingVersion).where(
            OnboardingVersion.cliente_id == client_id,
            OnboardingVersion.id == snapshot_id,
            OnboardingVersion.estado == COMPLETED,
        )
    )
    return _snapshot(row) if row else None


def get_current_snapshot(session: Session, client_id: UUID) -> SnapshotView | None:
    row = session.scalar(
        select(OnboardingVersion).where(
            OnboardingVersion.id == _latest_completed_id(client_id)
        )
    )
    return _snapshot(row) if row else None


def is_current_snapshot(session: Session, client_id: UUID, snapshot_id: UUID) -> bool:
    return session.scalar(select(_latest_completed_id(client_id))) == snapshot_id


def _editing(
    session: Session, client_id: UUID, base_id: UUID | None, revision: int | None
) -> tuple[date, OnboardingVersion | None, OnboardingVersion | None]:
    birth = lock_onboarding_client(session, client_id)
    if birth is None:
        raise OnboardingError(403)
    draft, completed = _versions(session, client_id)
    if (completed.id if completed else None) != base_id:
        raise OnboardingError(409)
    if (draft.revision if draft else None) != revision:
        raise OnboardingError(409)
    return birth, draft, completed


def _new_draft(
    session: Session,
    client_id: UUID,
    author_id: UUID,
    base: OnboardingVersion | None,
    data: dict[str, object],
) -> OnboardingVersion:
    row = OnboardingVersion(
        id=uuid4(),
        cliente_id=client_id,
        numero=base.numero + 1 if base else 1,
        estado=DRAFT,
        schema_version=1,
        dados=data,
        criado_por=author_id,
        revision=1,
    )
    session.add(row)
    return row


def start_initial_draft(
    session: Session, client_id: UUID, author_id: UUID
) -> OnboardingVersion:
    """Abre o primeiro rascunho sob o bloqueio do cadastro do cliente."""
    draft, completed = _versions(session, client_id)
    if completed is not None:
        raise OnboardingError(409)
    return (
        draft
        if draft is not None
        else _new_draft(session, client_id, author_id, None, {})
    )


def save_draft(
    session: Session, client_id: UUID, author_id: UUID, change: DraftChange
) -> DraftView:
    _, draft, completed = _editing(
        session, client_id, change.versao_base, change.revisao
    )
    patch = change.dados.model_dump(mode="json", exclude_unset=True)
    if draft is None:
        original = completed.dados if completed else {}
        draft = _new_draft(
            session, client_id, author_id, completed, {**original, **patch}
        )
    else:
        merged = {**draft.dados, **patch}
        if merged != draft.dados:
            draft.dados = merged
            draft.revision += 1
    return draft_view(draft)


def age_at(birth: date, today: date) -> int:
    return (
        today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    )


def _finalize(
    row: OnboardingVersion, data: OnboardingData, birth: date, author_id: UUID
) -> SnapshotView:
    now = utc_now()
    age = age_at(birth, now.astimezone(_ACADEMY_ZONE).date())
    if age < 0:
        raise OnboardingError(409)
    row.dados = data.model_dump(mode="json")
    row.estado = COMPLETED
    row.idade_snapshot = age
    row.concluido_em = now
    row.concluido_por = author_id
    row.revision += 1
    return _snapshot(row)


def complete_draft(
    session: Session, client_id: UUID, author_id: UUID, change: Completion
) -> SnapshotView:
    birth, draft, _ = _editing(session, client_id, change.versao_base, change.revisao)
    if draft is None:
        raise OnboardingError(409)
    try:
        data = OnboardingData.model_validate(draft.dados)
    except ValidationError:
        raise OnboardingError(422) from None
    return _finalize(draft, data, birth, author_id)


def confirm_update(
    session: Session, client_id: UUID, author_id: UUID, change: ConfirmUpdate
) -> SnapshotView:
    birth, draft, completed = _editing(
        session, client_id, change.versao_base, change.revisao
    )
    if draft is None:
        draft = _new_draft(session, client_id, author_id, completed, {})
    return _finalize(draft, change.dados, birth, author_id)


def append_evaluation(
    session: Session,
    client_id: UUID,
    instructor_id: UUID,
    snapshot_id: UUID,
    data: dict[str, object],
    *,
    evaluation_id: UUID | None = None,
) -> Evaluation:
    """Persiste avaliação do instrutor já autorizado pelo módulo chamador."""
    if get_snapshot(session, client_id, snapshot_id) is None:
        raise OnboardingError(404)
    evaluation = Evaluation(
        id=evaluation_id or uuid4(),
        cliente_id=client_id,
        instrutor_id=instructor_id,
        onboarding_id=snapshot_id,
        registrado_em=utc_now(),
        dados=data,
    )
    session.add(evaluation)
    return evaluation


def assessment_references(
    session: Session, client_id: UUID, snapshot_id: UUID
) -> list[tuple[UUID, datetime]]:
    """Referências de avaliações dentro do snapshot do cliente já autorizado."""
    return [
        (reference, when)
        for reference, when in session.execute(
            select(Evaluation.id, Evaluation.registrado_em)
            .where(
                Evaluation.cliente_id == client_id,
                Evaluation.onboarding_id == snapshot_id,
            )
            .order_by(Evaluation.registrado_em.desc(), Evaluation.id.desc())
        )
    ]

from typing import Annotated
from uuid import UUID, uuid5

from pydantic import BaseModel, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contracts.time import UtcTimestamp
from app.modules.assignments.service import Page, PostgresAssignmentReader
from app.modules.identity.models import Role
from app.modules.identity.roles import effective_roles
from app.modules.onboarding.models import Evaluation
from app.modules.onboarding.schemas import OnboardingData, PrivateInput
from app.modules.onboarding.service import (
    OnboardingError,
    append_evaluation,
    get_current_snapshot,
    get_snapshot,
    is_current_snapshot,
)
from app.modules.people.assignment_directory import AssignmentDirectory, ClientReference
from app.modules.people.onboarding_directory import lock_onboarding_client
from app.policies.access import Actor, Operation, allows


class CreateAssessment(PrivateInput):
    onboarding_id: UUID
    solicitacao_id: UUID
    observacao: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class AssessmentView(BaseModel):
    id: UUID
    onboarding_id: UUID
    instrutor_id: UUID
    instrutor_nome: str
    registrado_em: UtcTimestamp
    observacao: str | None


class AssessmentSnapshot(BaseModel):
    id: UUID
    numero: int
    dados: OnboardingData
    concluido_em: UtcTimestamp


class AssessmentHistory(BaseModel):
    cliente_nome: str
    snapshot: AssessmentSnapshot | None
    historico: Page[AssessmentView]


class AssessmentContext(BaseModel):
    snapshot_id: UUID
    idade_snapshot: int
    dados: OnboardingData
    avaliacao_id: UUID | None
    observacao_avaliacao: str | None


def _assigned_client(
    session: Session, actor: Actor, client_id: UUID
) -> ClientReference:
    if Role.INSTRUTOR not in actor.roles:
        raise OnboardingError(403)

    reader = PostgresAssignmentReader(session)
    # A troca de designação adquire o mesmo bloqueio da identidade do cliente.
    reader.directory.lock_people(actor.user_id, client_id)
    if not allows(
        actor, Operation.RECORD_ASSESSMENT, client_id=client_id, assignments=reader
    ):
        raise OnboardingError(403)
    return reader.directory.clients([client_id])[client_id]


def _note(row: Evaluation) -> str | None:
    value = row.dados.get("observacao")
    return value if isinstance(value, str) else None


def _view(row: Evaluation, name: str) -> AssessmentView:
    return AssessmentView(
        id=row.id,
        onboarding_id=row.onboarding_id,
        instrutor_id=row.instrutor_id,
        instrutor_nome=name,
        registrado_em=row.registrado_em,
        observacao=_note(row),
    )


def assessment_history(
    session: Session, actor: Actor, client_id: UUID, page: int, limit: int
) -> AssessmentHistory:
    client = _assigned_client(session, actor, client_id)
    base = select(Evaluation).where(Evaluation.cliente_id == client_id)
    total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = list(
        session.scalars(
            base.order_by(Evaluation.registrado_em.desc(), Evaluation.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    authors = AssignmentDirectory(session).instructor_names(
        list({row.instrutor_id for row in rows})
    )
    snapshot = get_current_snapshot(session, client_id)
    return AssessmentHistory(
        cliente_nome=client.nome,
        snapshot=AssessmentSnapshot.model_validate(snapshot, from_attributes=True)
        if snapshot
        else None,
        historico=Page[AssessmentView](
            itens=[_view(row, authors[row.instrutor_id]) for row in rows],
            pagina=page,
            limite=limit,
            total=total,
        ),
    )


def record_assessment(
    session: Session, actor: Actor, client_id: UUID, data: CreateAssessment
) -> AssessmentView:
    _assigned_client(session, actor, client_id)
    evaluation_id = uuid5(client_id, f"{actor.user_id}:{data.solicitacao_id}")
    existing = session.get(Evaluation, evaluation_id)
    if existing is not None:
        if (
            existing.cliente_id != client_id
            or existing.instrutor_id != actor.user_id
            or existing.onboarding_id != data.onboarding_id
            or _note(existing) != data.observacao
        ):
            raise OnboardingError(409)
        row = existing
    else:
        if get_snapshot(session, client_id, data.onboarding_id) is None:
            raise OnboardingError(404)
        if not is_current_snapshot(session, client_id, data.onboarding_id):
            raise OnboardingError(409)
        row = append_evaluation(
            session,
            client_id,
            actor.user_id,
            data.onboarding_id,
            {"observacao": data.observacao},
            evaluation_id=evaluation_id,
        )
    author = AssignmentDirectory(session).instructor_names([actor.user_id])
    return _view(row, author[actor.user_id])


def read_assessment_context(
    session: Session, actor: Actor, client_id: UUID, snapshot_id: UUID
) -> AssessmentContext:
    """Entrega contexto local tipado ao orquestrador a partir do cliente autenticado."""
    if not allows(actor, Operation.USE_AI_CONTEXT, client_id=client_id):
        raise OnboardingError(403)
    if lock_onboarding_client(
        session, client_id
    ) is None or Role.CLIENTE not in effective_roles(session, actor.user_id):
        raise OnboardingError(403)

    snapshot = get_snapshot(session, client_id, snapshot_id)
    if snapshot is None:
        raise OnboardingError(404)
    if not is_current_snapshot(session, client_id, snapshot_id):
        raise OnboardingError(409)
    row = session.scalar(
        select(Evaluation)
        .where(
            Evaluation.cliente_id == client_id,
            Evaluation.onboarding_id == snapshot_id,
        )
        .order_by(Evaluation.registrado_em.desc(), Evaluation.id.desc())
        .limit(1)
    )
    return AssessmentContext(
        snapshot_id=snapshot.id,
        idade_snapshot=snapshot.idade_snapshot,
        dados=snapshot.dados,
        avaliacao_id=row.id if row else None,
        observacao_avaliacao=_note(row) if row else None,
    )

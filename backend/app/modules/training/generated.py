"""Contrato interno de MOD-04 para publicação tecnicamente validada por MOD-06."""

from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contracts.training.generated import ValidatedGeneration
from app.modules.assignments.service import PostgresAssignmentReader
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.notifications.service import notify_workout_review
from app.modules.training.publication import _audit, _expire
from app.modules.training.workout_models import WorkoutValidation, WorkoutVersion
from app.modules.training.workouts import (
    WorkoutError,
    _build_days,
    _current_id,
    _references,
    _version,
    retention_candidates,
)
from app.policies.access import Actor, Operation, allows


def lock_generation_client(session: Session, actor: Actor, client_id: UUID) -> Actor:
    reader = PostgresAssignmentReader(session)
    reader.directory.lock_people(actor.user_id, client_id)
    fresh = Actor(actor.user_id, effective_roles(session, actor.user_id))
    operation = (
        Operation.USE_AI_CONTEXT
        if actor.user_id == client_id
        else Operation.PRESCRIBE_WORKOUT
    )
    client = reader.directory.clients([client_id]).get(client_id)
    if (
        not client
        or not client.elegivel
        or not allows(fresh, operation, client_id=client_id, assignments=reader)
    ):
        raise WorkoutError(403)
    return fresh


def current_generation_base(
    session: Session, actor: Actor, client_id: UUID
) -> UUID | None:
    lock_generation_client(session, actor, client_id)
    return _current_id(session, client_id)


def publish_generated(
    session: Session, actor: Actor, client_id: UUID, data: ValidatedGeneration
) -> UUID:
    actor = lock_generation_client(session, actor, client_id)
    id = uuid5(data.execution_id, "ficha")
    existing = session.get(WorkoutVersion, id)
    if existing is not None:
        if existing.cliente_id != client_id or existing.origem != "IA":
            raise WorkoutError(409)
        return id
    _references(session, client_id, data.content)
    if (
        data.base_id != _current_id(session, client_id)
        or not data.content.dias
        or any(not d.itens for d in data.content.dias)
    ):
        raise WorkoutError(409)
    days = _build_days(session, data.content)
    number = (
        session.scalar(
            select(func.max(WorkoutVersion.numero)).where(
                WorkoutVersion.cliente_id == client_id
            )
        )
        or 0
    )
    row = WorkoutVersion(
        id=id,
        cliente_id=client_id,
        numero=number + 1,
        origem="IA",
        autor_id=None,
        onboarding_id=data.content.onboarding_id,
        avaliacao_id=None,
        versao_base_id=data.base_id,
        estado_publicacao="RASCUNHO",
        vigente=False,
        revision=1,
        dias=days,
        explicacao=data.explanation,
    )
    session.add(row)
    session.flush()
    now = utc_now()
    session.add(
        WorkoutValidation(
            versao_id=id,
            solicitacao_id=data.execution_id,
            validado_por=actor.user_id,
            revisao=1,
            restricoes_conferidas=True,
            validado_em=now,
        )
    )
    if data.base_id:
        previous = _version(session, client_id, data.base_id)
        previous.vigente = False
        previous.estado_publicacao = "SUBSTITUIDO"
        session.flush()
    row.estado_publicacao, row.vigente, row.publicada_em = "PUBLICADO", True, now
    session.flush()
    for old in retention_candidates(session, client_id):
        _expire(
            session,
            actor,
            _version(session, client_id, old),
            data.execution_id,
            "LIMITE_15",
        )
    recipient = PostgresAssignmentReader(session).review_recipient(client_id)
    notify_workout_review(
        session, uuid5(id, "publicacao"), recipient.id if recipient else None
    )
    _audit(session, actor, row, data.execution_id, "workout.published")
    return id

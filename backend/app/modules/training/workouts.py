from uuid import UUID, uuid4, uuid5

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.events.contracts import AuditEvent
from app.modules.assignments.service import PostgresAssignmentReader
from app.modules.audit.service import record_audit
from app.modules.equipment.service import available_resources
from app.modules.identity.models import Role
from app.modules.identity.service import utc_now
from app.modules.onboarding.service import assessment_references, get_current_snapshot
from app.modules.training.catalog import (
    CatalogError,
    eligible_exercises,
    require_prescribable,
)
from app.modules.training.workout_models import WorkoutDay, WorkoutItem, WorkoutVersion
from app.modules.training.workout_schemas import (
    AssessmentReference,
    CreateWorkout,
    UpdateWorkout,
    WorkoutContent,
    WorkoutContext,
    WorkoutDayInput,
    WorkoutDayView,
    WorkoutEquipment,
    WorkoutItemInput,
    WorkoutItemView,
    WorkoutMeta,
    WorkoutOnboarding,
    WorkoutPage,
    WorkoutView,
)
from app.policies.access import Actor, Operation, allows


class WorkoutError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _authorize(session: Session, actor: Actor, client_id: UUID) -> str:
    if Role.INSTRUTOR not in actor.roles:
        raise WorkoutError(403)
    reader = PostgresAssignmentReader(session)
    reader.directory.lock_people(actor.user_id, client_id)
    if not allows(
        actor, Operation.PRESCRIBE_WORKOUT, client_id=client_id, assignments=reader
    ):
        raise WorkoutError(403)
    return reader.directory.clients([client_id])[client_id].nome


def _query() -> Select[WorkoutVersion]:
    return (
        select(WorkoutVersion)
        .options(joinedload(WorkoutVersion.dias).joinedload(WorkoutDay.itens))
        .execution_options(populate_existing=True)
    )


def _version(session: Session, client_id: UUID, version_id: UUID) -> WorkoutVersion:
    row = (
        session.scalars(
            _query().where(
                WorkoutVersion.id == version_id,
                WorkoutVersion.cliente_id == client_id,
            )
        )
        .unique()
        .one_or_none()
    )
    if row is None:
        raise WorkoutError(404)
    return row


def _meta(row: WorkoutVersion) -> WorkoutMeta:
    return WorkoutMeta.model_validate(
        {
            **{
                field: getattr(row, field)
                for field in WorkoutMeta.model_fields
                if field != "revisao"
            },
            "revisao": row.revision,
        }
    )


def _item(row: WorkoutItem) -> WorkoutItemInput:
    return WorkoutItemInput.model_validate(
        {
            "exercicio_id": row.exercicio_id,
            "equipamento_ids": row.exercicio_snapshot.get("equipamento_ids", []),
            "series": row.series,
            "repeticoes": row.repeticoes,
            "carga_kg": row.carga_kg,
            "intervalo_segundos": row.intervalo_segundos,
            "cadencia": row.cadencia,
            "observacoes": row.observacoes,
        }
    )


def _view(row: WorkoutVersion) -> WorkoutView:
    days = (
        []
        if row.conteudo_excluido_em
        else [
            WorkoutDayView(
                titulo=day.titulo,
                itens=[
                    WorkoutItemView(
                        **_item(item).model_dump(),
                        exercicio_snapshot=item.exercicio_snapshot,
                    )
                    for item in day.itens
                ],
            )
            for day in row.dias
        ]
    )
    return WorkoutView(**_meta(row).model_dump(), dias=days)


def _current_id(session: Session, client_id: UUID) -> UUID | None:
    return session.scalar(
        select(WorkoutVersion.id).where(
            WorkoutVersion.cliente_id == client_id,
            WorkoutVersion.vigente.is_(True),
        )
    )


def workout_context(session: Session, actor: Actor, client_id: UUID) -> WorkoutContext:
    name = _authorize(session, actor, client_id)
    snapshot = get_current_snapshot(session, client_id)
    references = (
        assessment_references(session, client_id, snapshot.id) if snapshot else []
    )
    return WorkoutContext(
        cliente_nome=name,
        onboarding=WorkoutOnboarding(id=snapshot.id, numero=snapshot.numero)
        if snapshot
        else None,
        avaliacoes=[
            AssessmentReference(id=reference, registrado_em=when)
            for reference, when in references
        ],
        exercicios=eligible_exercises(session),
        equipamentos=[
            WorkoutEquipment(id=item.id, nome=item.nome)
            for item in available_resources(session)
        ],
        versao_atual_id=_current_id(session, client_id),
    )


def workout_history(
    session: Session,
    actor: Actor,
    client_id: UUID,
    page: int,
    limit: int,
) -> WorkoutPage:
    _authorize(session, actor, client_id)
    query = select(WorkoutVersion).where(WorkoutVersion.cliente_id == client_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.scalars(
        query.order_by(WorkoutVersion.numero.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return WorkoutPage(
        itens=[_meta(row) for row in rows], pagina=page, limite=limit, total=total
    )


def get_workout(
    session: Session, actor: Actor, client_id: UUID, version_id: UUID
) -> WorkoutView:
    _authorize(session, actor, client_id)
    return _view(_version(session, client_id, version_id))


def _references(session: Session, client_id: UUID, content: WorkoutContent) -> None:
    snapshot = get_current_snapshot(session, client_id)
    if snapshot is None or snapshot.id != content.onboarding_id:
        raise WorkoutError(409)
    if content.avaliacao_id is not None and content.avaliacao_id not in {
        reference
        for reference, _ in assessment_references(session, client_id, snapshot.id)
    }:
        raise WorkoutError(422)


def _build_days(session: Session, content: WorkoutContent) -> list[WorkoutDay]:
    selected = {
        (item.exercicio_id, tuple(item.equipamento_ids))
        for day in content.dias
        for item in day.itens
    }
    try:
        snapshots = {
            key: require_prescribable(session, key[0], key[1])
            for key in sorted(selected)
        }
    except CatalogError as exc:
        raise WorkoutError(exc.status) from None
    return [
        WorkoutDay(
            id=uuid4(),
            ordem=order,
            titulo=day.titulo,
            itens=[
                WorkoutItem(
                    id=uuid4(),
                    ordem=position,
                    exercicio_id=item.exercicio_id,
                    series=item.series,
                    repeticoes=item.repeticoes,
                    carga_kg=item.carga_kg,
                    intervalo_segundos=item.intervalo_segundos,
                    cadencia=item.cadencia,
                    observacoes=item.observacoes,
                    exercicio_snapshot=snapshots[
                        (item.exercicio_id, tuple(item.equipamento_ids))
                    ],
                )
                for position, item in enumerate(day.itens, 1)
            ],
        )
        for order, day in enumerate(content.dias, 1)
    ]


def _content(row: WorkoutVersion) -> WorkoutContent:
    return WorkoutContent(
        onboarding_id=row.onboarding_id,
        avaliacao_id=row.avaliacao_id,
        dias=[
            WorkoutDayInput(
                titulo=day.titulo, itens=[_item(item) for item in day.itens]
            )
            for day in row.dias
        ],
    )


def _audit(
    session: Session, actor: Actor, row: WorkoutVersion, correlation: UUID, action: str
) -> None:
    record_audit(
        session,
        AuditEvent(
            id=uuid4(),
            actor_id=actor.user_id,
            action=action,
            resource_type="versao_ficha",
            resource_id=row.id,
            correlation_id=correlation,
            occurred_at=utc_now(),
        ),
    )


def create_draft(
    session: Session,
    actor: Actor,
    client_id: UUID,
    data: CreateWorkout,
    correlation: UUID,
) -> WorkoutView:
    _authorize(session, actor, client_id)
    version_id = uuid5(client_id, f"{actor.user_id}:{data.solicitacao_id}")
    existing = session.get(WorkoutVersion, version_id)
    if existing is not None:
        content = WorkoutContent(
            onboarding_id=data.onboarding_id,
            avaliacao_id=data.avaliacao_id,
            dias=data.dias,
        )
        existing = _version(session, client_id, version_id)
        if (
            existing.revision != 1
            or existing.versao_base_id != data.versao_base_id
            or _content(existing) != content
        ):
            raise WorkoutError(409)
        return _view(existing)
    _references(session, client_id, data)
    if data.versao_base_id != _current_id(session, client_id):
        raise WorkoutError(409)
    days = _build_days(session, data)
    number = (
        session.scalar(
            select(func.max(WorkoutVersion.numero)).where(
                WorkoutVersion.cliente_id == client_id
            )
        )
        or 0
    )
    row = WorkoutVersion(
        id=version_id,
        cliente_id=client_id,
        numero=number + 1,
        origem="MANUAL",
        autor_id=actor.user_id,
        onboarding_id=data.onboarding_id,
        avaliacao_id=data.avaliacao_id,
        versao_base_id=data.versao_base_id,
        estado_publicacao="RASCUNHO",
        vigente=False,
        revision=1,
        dias=days,
    )
    session.add(row)
    session.flush()
    _audit(session, actor, row, correlation, "workout.draft_created")
    return _view(row)


def update_draft(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
    data: UpdateWorkout,
    correlation: UUID,
) -> WorkoutView:
    _authorize(session, actor, client_id)
    row = _version(session, client_id, version_id)
    if row.estado_publicacao != "RASCUNHO" or row.revision != data.revisao:
        raise WorkoutError(409)
    if row.autor_id != actor.user_id:
        raise WorkoutError(403)
    _references(session, client_id, data)
    days = _build_days(session, data)
    row.dias.clear()
    session.flush()
    row.onboarding_id = data.onboarding_id
    row.avaliacao_id = data.avaliacao_id
    row.revision += 1
    row.dias = days
    session.flush()
    _audit(session, actor, row, correlation, "workout.draft_updated")
    return _view(row)


def retention_candidates(session: Session, client_id: UUID) -> list[UUID]:
    """Seleciona conteúdo excedente para o serviço transacional de publicação."""
    return list(
        session.scalars(
            select(WorkoutVersion.id)
            .where(
                WorkoutVersion.cliente_id == client_id,
                WorkoutVersion.estado_publicacao.in_(("PUBLICADO", "SUBSTITUIDO")),
                WorkoutVersion.conteudo_excluido_em.is_(None),
            )
            .order_by(WorkoutVersion.vigente.desc(), WorkoutVersion.numero.desc())
            .offset(15)
        )
    )

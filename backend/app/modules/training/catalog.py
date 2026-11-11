from collections.abc import Collection, Sequence
from uuid import UUID, uuid4

from psycopg.errors import UniqueViolation
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.equipment.service import (
    EquipmentResource,
    EquipmentUnavailable,
    read_resources,
    require_available,
)
from app.modules.identity.service import utc_now
from app.modules.training.models import (
    Exercise,
    ExerciseResource,
    ExerciseResourceGroup,
)
from app.modules.training.schemas import (
    ExerciseCandidate,
    ExerciseEquipment,
    ExerciseFields,
    ExercisePage,
    ExerciseSummary,
    ExerciseUpdate,
    ExerciseView,
    normalize_name,
)


class CatalogError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def available_combinations(
    dispensa: bool,
    groups: Sequence[Sequence[UUID]],
    available: Collection[UUID],
) -> list[list[UUID]]:
    if dispensa:
        return [] if groups else [[]]
    return [
        list(group)
        for group in groups
        if group and all(item in available for item in group)
    ]


def _query() -> Select[Exercise]:
    return (
        select(Exercise)
        .options(joinedload(Exercise.grupos).joinedload(ExerciseResourceGroup.recursos))
        .execution_options(populate_existing=True)
    )


def _row(
    session: Session, exercise_id: UUID, *, lock: bool = False, shared: bool = False
) -> Exercise:
    if lock:
        locked = session.scalar(
            select(Exercise.id)
            .where(Exercise.id == exercise_id)
            .with_for_update(read=shared)
        )
        if locked is None:
            raise CatalogError(404)
    row = (
        session.scalars(_query().where(Exercise.id == exercise_id))
        .unique()
        .one_or_none()
    )
    if row is None:
        raise CatalogError(404)
    return row


def _combinations(row: Exercise) -> list[list[UUID]]:
    return [[item.equipamento_id for item in group.recursos] for group in row.grupos]


def _inventory(
    session: Session, rows: Sequence[Exercise]
) -> dict[UUID, EquipmentResource]:
    return read_resources(
        session,
        {
            item.equipamento_id
            for row in rows
            for group in row.grupos
            for item in group.recursos
        },
    )


def _available(resources: dict[UUID, EquipmentResource]) -> set[UUID]:
    return {resource.id for resource in resources.values() if resource.disponivel}


def _summary(row: Exercise) -> ExerciseSummary:
    return ExerciseSummary(
        id=row.id,
        nome=row.nome,
        descricao=row.descricao,
        grupo_muscular=row.grupo_muscular,
        dispensa_equipamento=row.dispensa_equipamento,
    )


def _view(row: Exercise, resources: dict[UUID, EquipmentResource]) -> ExerciseView:
    groups = _combinations(row)
    return ExerciseView(
        **_summary(row).model_dump(),
        ativo=row.ativo,
        revisao=row.revision,
        elegivel=row.ativo
        and bool(
            available_combinations(
                row.dispensa_equipamento,
                groups,
                _available(resources),
            )
        ),
        combinacoes=[
            [
                ExerciseEquipment(
                    id=equipment_id,
                    nome=resources[equipment_id].nome
                    if equipment_id in resources
                    else "Equipamento indisponível",
                    disponivel=equipment_id in resources
                    and resources[equipment_id].disponivel,
                )
                for equipment_id in group
            ]
            for group in groups
        ],
    )


def exercise_detail(session: Session, exercise_id: UUID) -> ExerciseView:
    row = _row(session, exercise_id)
    return _view(row, _inventory(session, [row]))


def catalog_page(session: Session, page: int, limit: int) -> ExercisePage[ExerciseView]:
    total = session.scalar(select(func.count()).select_from(Exercise)) or 0
    rows = list(
        session.scalars(
            _query()
            .order_by(Exercise.nome_normalizado, Exercise.id)
            .offset((page - 1) * limit)
            .limit(limit)
        ).unique()
    )
    resources = _inventory(session, rows)
    return ExercisePage[ExerciseView](
        itens=[_view(row, resources) for row in rows],
        pagina=page,
        limite=limit,
        total=total,
    )


def eligible_exercises(session: Session) -> list[ExerciseCandidate]:
    """Catálogo viável para nova seleção, consultado pelo MOD-04 ou MOD-06."""
    rows = list(
        session.scalars(
            _query()
            .where(Exercise.ativo.is_(True))
            .order_by(Exercise.nome_normalizado, Exercise.id)
        ).unique()
    )
    available = _available(_inventory(session, rows))
    candidates = []
    for row in rows:
        viable = available_combinations(
            row.dispensa_equipamento, _combinations(row), available
        )
        if viable:
            candidates.append(
                ExerciseCandidate(
                    **_summary(row).model_dump(),
                    combinacoes_disponiveis=viable,
                )
            )
    return candidates


def require_prescribable(
    session: Session,
    exercise_id: UUID,
    equipment_ids: Sequence[UUID],
) -> dict[str, object]:
    """Confere a alternativa escolhida dentro da transação de gravação da ficha."""
    row = _row(session, exercise_id, lock=True, shared=True)
    chosen = frozenset(equipment_ids)
    groups = _combinations(row)
    if not row.ativo or len(chosen) != len(equipment_ids):
        raise CatalogError(409)
    if row.dispensa_equipamento:
        valid = not groups and not chosen
    else:
        valid = bool(chosen) and any(frozenset(group) == chosen for group in groups)
    if not valid:
        raise CatalogError(409)
    try:
        require_available(session, chosen)
    except EquipmentUnavailable:
        raise CatalogError(409) from None
    snapshot = _summary(row).model_dump(mode="json")
    snapshot["catalogo_revisao"] = row.revision
    snapshot["equipamento_ids"] = [str(value) for value in sorted(chosen)]
    return snapshot


def _save(
    session: Session,
    row: Exercise,
    data: ExerciseFields,
    actor_id: UUID,
    correlation_id: UUID,
    action: str,
) -> ExerciseView:
    ids = {equipment_id for group in data.combinacoes for equipment_id in group}
    resources = read_resources(session, ids)
    if ids != resources.keys():
        raise CatalogError(422)
    row.nome = data.nome
    row.nome_normalizado = normalize_name(data.nome)
    row.descricao = data.descricao
    row.grupo_muscular = data.grupo_muscular
    row.dispensa_equipamento = data.dispensa_equipamento
    row.ativo = data.ativo
    row.grupos = [
        ExerciseResourceGroup(
            id=uuid4(),
            recursos=[
                ExerciseResource(id=uuid4(), equipamento_id=equipment_id)
                for equipment_id in sorted(group)
            ],
        )
        for group in data.combinacoes
    ]
    session.add(row)
    try:
        session.flush()
    except IntegrityError as exc:
        if (
            isinstance(exc.orig, UniqueViolation)
            and exc.orig.diag.constraint_name == "uq_exercicio_nome_normalizado"
        ):
            raise CatalogError(409) from None
        raise
    record_audit(
        session,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            resource_type="exercicio",
            resource_id=row.id,
            correlation_id=correlation_id,
            occurred_at=utc_now(),
        ),
    )
    return _view(row, resources)


def create_exercise(
    session: Session,
    data: ExerciseFields,
    actor_id: UUID,
    correlation_id: UUID,
) -> ExerciseView:
    row = Exercise(id=uuid4(), revision=1)
    return _save(session, row, data, actor_id, correlation_id, "exercise.created")


def update_exercise(
    session: Session,
    exercise_id: UUID,
    data: ExerciseUpdate,
    actor_id: UUID,
    correlation_id: UUID,
) -> ExerciseView:
    row = _row(session, exercise_id, lock=True)
    if row.revision != data.revisao:
        raise CatalogError(409)
    action = "exercise.updated"
    if row.ativo != data.ativo:
        action = "exercise.reactivated" if data.ativo else "exercise.deactivated"
    row.revision += 1
    return _save(session, row, data, actor_id, correlation_id, action)

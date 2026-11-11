"""Publicação manual, parecer imutável e retenção em uma transação por cliente."""

from uuid import UUID, uuid4, uuid5

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.events.contracts import AuditEvent
from app.modules.assignments.service import PostgresAssignmentReader, my_clients
from app.modules.audit.service import record_audit
from app.modules.identity.models import Role
from app.modules.identity.service import utc_now
from app.modules.notifications.email import (
    DeliveryResult,
    EmailRequest,
    local_email_delivery,
)
from app.modules.notifications.models import EmailKind
from app.modules.notifications.service import notify_workout_review
from app.modules.training.catalog import CatalogError, require_prescribable
from app.modules.training.review_schemas import (
    OpinionView,
    PublishWorkout,
    ReviewDetail,
    ReviewQueue,
    ReviewQueueItem,
    ReviewWorkout,
    ValidationView,
)
from app.modules.training.workout_models import (
    WorkoutDay,
    WorkoutItem,
    WorkoutOpinion,
    WorkoutValidation,
    WorkoutVersion,
)
from app.modules.training.workouts import (
    WorkoutError,
    _authorize,
    _content,
    _current_id,
    _item,
    _references,
    _version,
    _view,
    retention_candidates,
)
from app.policies.access import Actor, Operation, allows


def _opinion(session: Session, version_id: UUID) -> WorkoutOpinion | None:
    return session.scalar(
        select(WorkoutOpinion).where(
            WorkoutOpinion.versao_id == version_id,
            WorkoutOpinion.estado.in_(("ACEITO", "REJEITADO")),
        )
    )


def detail(session: Session, row: WorkoutVersion) -> ReviewDetail:
    opinion = _opinion(session, row.id)
    validation = session.get(WorkoutValidation, row.id)
    return ReviewDetail(
        ficha=_view(row),
        parecer=OpinionView(
            id=opinion.id,
            estado=opinion.estado,
            instrutor_id=opinion.instrutor_id,
            criado_em=opinion.criado_em,
            motivo=opinion.motivo,
        )
        if opinion
        else OpinionView(),
        validacao=ValidationView(
            revisao=validation.revisao,
            validado_por=validation.validado_por,
            validado_em=validation.validado_em,
        )
        if validation
        else None,
    )


def review_detail(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
) -> ReviewDetail:
    _authorize(session, actor, client_id)
    return detail(session, _version(session, client_id, version_id))


def _read_access(session: Session, actor: Actor, client_id: UUID) -> None:
    reader = PostgresAssignmentReader(session)
    reader.directory.lock_people(actor.user_id, client_id)
    client = reader.directory.clients([client_id]).get(client_id)
    if (
        not client
        or not client.elegivel
        or not allows(
            actor,
            Operation.READ_WORKOUT,
            client_id=client_id,
            assignments=reader,
        )
    ):
        raise WorkoutError(403)


def published_workout(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID | None = None,
) -> ReviewDetail | None:
    """Contrato de leitura compartilhável com chat/exportação, sem cache de conteúdo."""
    _read_access(session, actor, client_id)
    target = version_id if version_id is not None else _current_id(session, client_id)
    if target is None:
        return None
    row = _version(session, client_id, target)
    if row.estado_publicacao == "RASCUNHO":
        raise WorkoutError(404)
    return detail(session, row)


def _audit(
    session: Session,
    actor: Actor,
    row: WorkoutVersion,
    correlation: UUID,
    action: str,
    reason: str | None = None,
) -> None:
    record_audit(
        session,
        AuditEvent(
            id=uuid4(),
            actor_id=actor.user_id,
            action=action,
            resource_type="versao_ficha",
            resource_id=row.id,
            reason_code=reason.lower() if reason else None,
            correlation_id=correlation,
            occurred_at=utc_now(),
        ),
    )


def _expire(
    session: Session,
    actor: Actor,
    row: WorkoutVersion,
    correlation: UUID,
    reason: str,
) -> None:
    if row.conteudo_excluido_em is not None:
        return
    if row.vigente or row.estado_publicacao == "RASCUNHO":
        raise WorkoutError(409)
    row.explicacao = None
    row.estado_publicacao = "CONTEUDO_EXPIRADO"
    row.conteudo_excluido_em = utc_now()
    row.motivo_exclusao = reason
    session.flush()
    # O gatilho permite DELETE somente depois da expiração da versão.
    day_ids = select(WorkoutDay.id).where(WorkoutDay.versao_id == row.id)
    session.execute(delete(WorkoutItem).where(WorkoutItem.dia_id.in_(day_ids)))
    session.execute(delete(WorkoutDay).where(WorkoutDay.versao_id == row.id))
    session.expire(row, ["dias"])
    _audit(session, actor, row, correlation, "workout.content_expired", reason)


def _validate_manual(session: Session, row: WorkoutVersion) -> None:
    if row.origem != "MANUAL":
        # IA terá seu próprio contrato validado em AI-03. Não pode usar este atalho.
        raise WorkoutError(409)
    content = _content(row)
    _references(session, row.cliente_id, content)
    if not content.dias or any(not day.itens for day in content.dias):
        raise WorkoutError(422)
    items = {
        (item.exercicio_id, tuple(item.equipamento_ids))
        for day in content.dias
        for item in day.itens
    }
    try:
        snapshots = {
            key: require_prescribable(session, key[0], key[1]) for key in sorted(items)
        }
    except CatalogError as exc:
        raise WorkoutError(exc.status) from None
    if any(
        item.exercicio_snapshot
        != snapshots[(item.exercicio_id, tuple(_item(item).equipamento_ids))]
        for day in row.dias
        for item in day.itens
    ):
        raise WorkoutError(409)


def publish_manual(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
    data: PublishWorkout,
    correlation: UUID,
) -> ReviewDetail:
    _authorize(session, actor, client_id)
    row = _version(session, client_id, version_id)
    existing = session.get(WorkoutValidation, row.id)
    if existing is not None:
        if (
            existing.solicitacao_id != data.solicitacao_id
            or existing.validado_por != actor.user_id
            or existing.revisao != data.revisao
            or row.onboarding_id != data.onboarding_id
            or row.versao_base_id != data.versao_base_id
        ):
            raise WorkoutError(409)
        # Repetir uma publicação não troca novamente a vigente nem reaplica expurgo.
        return detail(session, row)
    if row.autor_id != actor.user_id:
        raise WorkoutError(403)
    if (
        row.estado_publicacao != "RASCUNHO"
        or row.revision != data.revisao
        or row.onboarding_id != data.onboarding_id
        or row.versao_base_id != data.versao_base_id
        or _current_id(session, client_id) != row.versao_base_id
    ):
        raise WorkoutError(409)
    _validate_manual(session, row)
    now = utc_now()
    session.add(
        WorkoutValidation(
            versao_id=row.id,
            solicitacao_id=data.solicitacao_id,
            validado_por=actor.user_id,
            revisao=row.revision,
            restricoes_conferidas=True,
            validado_em=now,
        )
    )
    if row.versao_base_id is not None:
        previous = _version(session, client_id, row.versao_base_id)
        previous.vigente = False
        previous.estado_publicacao = "SUBSTITUIDO"
        session.flush()
    row.vigente = True
    row.estado_publicacao = "PUBLICADO"
    row.publicada_em = now
    session.flush()
    for old_id in retention_candidates(session, client_id):
        _expire(
            session,
            actor,
            _version(session, client_id, old_id),
            correlation,
            "LIMITE_15",
        )
    recipient = PostgresAssignmentReader(session).review_recipient(client_id)
    notify_workout_review(
        session,
        uuid5(row.id, "publicacao"),
        recipient.id if recipient else None,
    )
    _audit(session, actor, row, correlation, "workout.published")
    return detail(session, row)


def record_opinion(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
    data: ReviewWorkout,
    correlation: UUID,
) -> ReviewDetail:
    _authorize(session, actor, client_id)
    row = _version(session, client_id, version_id)
    opinion_id = uuid5(row.id, f"{actor.user_id}:{data.solicitacao_id}")
    existing = _opinion(session, row.id)
    if existing is not None:
        if (
            existing.id != opinion_id
            or existing.estado != data.estado
            or existing.motivo != data.motivo
        ):
            raise WorkoutError(409)
        return detail(session, row)
    if row.estado_publicacao not in ("PUBLICADO", "SUBSTITUIDO"):
        raise WorkoutError(409)
    session.add(
        WorkoutOpinion(
            id=opinion_id,
            versao_id=row.id,
            instrutor_id=actor.user_id,
            estado=data.estado,
            motivo=data.motivo,
            criado_em=utc_now(),
        )
    )
    session.flush()
    if data.estado == "REJEITADO":
        rejected = list(
            session.scalars(
                select(WorkoutVersion)
                .join(WorkoutOpinion, WorkoutOpinion.versao_id == WorkoutVersion.id)
                .where(
                    WorkoutVersion.cliente_id == client_id,
                    WorkoutOpinion.estado == "REJEITADO",
                )
                .order_by(WorkoutVersion.numero.desc())
            )
        )
        # Ordenar pela versão, não pela hora de chegada do parecer.
        for old in rejected[1:]:
            _expire(session, actor, old, correlation, "REJEITADA_ANTERIOR")
    _audit(
        session,
        actor,
        row,
        correlation,
        "workout.accepted" if data.estado == "ACEITO" else "workout.rejected",
    )
    return detail(session, row)


def review_queue(
    session: Session,
    actor: Actor,
    page: int,
    limit: int,
) -> ReviewQueue:
    if Role.INSTRUTOR not in actor.roles:
        raise WorkoutError(403)
    assigned = my_clients(session, actor.user_id, 1, 2_147_483_647).itens
    names = {item.id: item.nome for item in assigned}
    # Bloqueia e revalida designações antes de ler conteúdo protegido.
    PostgresAssignmentReader(session).directory.lock_people(
        actor.user_id, *sorted(names)
    )
    eligible = []
    for client_id in sorted(names):
        try:
            _authorize(session, actor, client_id)
        except WorkoutError:
            continue
        eligible.append(client_id)
    reviewed = (
        select(WorkoutOpinion.id)
        .where(
            WorkoutOpinion.versao_id == WorkoutVersion.id,
            WorkoutOpinion.estado.in_(("ACEITO", "REJEITADO")),
        )
        .exists()
    )
    query = select(WorkoutVersion).where(
        WorkoutVersion.cliente_id.in_(eligible),
        WorkoutVersion.estado_publicacao.in_(("PUBLICADO", "SUBSTITUIDO")),
        ~reviewed,
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.scalars(
        query.order_by(WorkoutVersion.publicada_em, WorkoutVersion.id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return ReviewQueue(
        itens=[
            ReviewQueueItem(
                cliente_id=row.cliente_id,
                cliente_nome=names[row.cliente_id],
                versao_id=row.id,
                numero=row.numero,
                publicada_em=row.publicada_em,
            )
            for row in rows
        ],
        pagina=page,
        limite=limit,
        total=total,
    )


def send_review_notice(
    sessions: sessionmaker[Session],
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
    *,
    retry_after: int | None = None,
) -> DeliveryResult | None:
    with sessions.begin() as session:
        _authorize(session, actor, client_id)
        row = _version(session, client_id, version_id)
        if row.estado_publicacao not in ("PUBLICADO", "SUBSTITUIDO") or _opinion(
            session, row.id
        ):
            return None
        recipient = PostgresAssignmentReader(session).review_recipient(client_id)
        if recipient is None:
            return None
        request = EmailRequest(
            event_id=uuid5(row.id, "publicacao"),
            recipient_id=recipient.id,
            kind=EmailKind.TREINO_PARA_AVALIAR,
            address=recipient.email,
            body=(
                "Há uma ficha aguardando seu parecer. "
                "Acesse a fila de avaliação no AcademIA."
            ),
        )
        notify_workout_review(session, request.event_id, recipient.id)
    # Nenhum I/O externo ocorre dentro da transação da publicação.
    return local_email_delivery(sessions).send(request, retry_after=retry_after)

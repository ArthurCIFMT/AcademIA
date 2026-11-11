"""Leitura/exportação de prescrições retidas; disponibilidade não reescreve conteúdo."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.equipment.service import read_resources
from app.modules.identity.service import utc_now
from app.modules.training.publication import _read_access, detail
from app.modules.training.published_schemas import (
    PublishedHistory,
    PublishedSummary,
    PublishedWorkout,
    ResourceStatus,
)
from app.modules.training.workout_models import WorkoutOpinion, WorkoutVersion
from app.modules.training.workouts import WorkoutError, _version
from app.policies.access import Actor


def published_history(
    session: Session,
    actor: Actor,
    client_id: UUID,
) -> PublishedHistory:
    _read_access(session, actor, client_id)
    opinion = (
        select(WorkoutOpinion.estado)
        .where(
            WorkoutOpinion.versao_id == WorkoutVersion.id,
            WorkoutOpinion.estado.in_(("ACEITO", "REJEITADO")),
        )
        .scalar_subquery()
    )
    rows = session.execute(
        select(WorkoutVersion, opinion)
        .where(
            WorkoutVersion.cliente_id == client_id,
            WorkoutVersion.estado_publicacao.in_(("PUBLICADO", "SUBSTITUIDO")),
            WorkoutVersion.conteudo_excluido_em.is_(None),
        )
        .order_by(WorkoutVersion.vigente.desc(), WorkoutVersion.numero.desc())
        .limit(15)
    )
    items = [
        PublishedSummary(
            id=row.id,
            numero=row.numero,
            origem=row.origem,
            autor_id=row.autor_id,
            publicada_em=row.publicada_em,
            vigente=row.vigente,
            parecer_estado=state or "PENDENTE",
        )
        for row, state in rows
    ]
    return PublishedHistory(
        versao_vigente_id=next((item.id for item in items if item.vigente), None),
        itens=items,
    )


def read_published(
    session: Session,
    actor: Actor,
    client_id: UUID,
    version_id: UUID,
) -> PublishedWorkout:
    _read_access(session, actor, client_id)
    row = _version(session, client_id, version_id)
    if (
        row.estado_publicacao not in ("PUBLICADO", "SUBSTITUIDO")
        or row.conteudo_excluido_em
    ):
        raise WorkoutError(404)
    content = detail(session, row)
    ids = {
        equipment_id
        for day in content.ficha.dias
        for item in day.itens
        for equipment_id in item.equipamento_ids
    }
    resources = read_resources(session, ids, lock=True)
    return PublishedWorkout(
        **content.model_dump(),
        consultado_em=utc_now(),
        equipamentos=[
            ResourceStatus(
                id=resource_id,
                nome=resources[resource_id].nome
                if resource_id in resources
                else "Equipamento não encontrado",
                disponivel=resource_id in resources
                and resources[resource_id].disponivel,
            )
            for resource_id in sorted(ids)
        ],
    )

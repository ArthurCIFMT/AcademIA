from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta
from hashlib import sha256
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.modules.access.authorization.contracts import DecisionReason, DecisionView
from app.modules.access.authorization.models import AccessDecision, TurnstileCommand
from app.modules.access.events.models import AccessEvent
from app.modules.access.integrations.turnstile.contracts import (
    AccessSettings,
    Command,
    DeliveryFailure,
    Passage,
)
from app.modules.identity.models import Role
from app.modules.identity.roles import effective_roles
from app.modules.memberships.service import ValidMembership, valid_membership
from app.modules.people.assignment_directory import AssignmentDirectory

_ACADEMY_ZONE = ZoneInfo("America/Sao_Paulo")
_PASSAGE_ORIGIN = "CATRACA_SIMULADA"


class AccessError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def academy_window(at: datetime) -> tuple[datetime, datetime]:
    day = academy_date(at)
    return (
        datetime.combine(day, time.min, tzinfo=_ACADEMY_ZONE).astimezone(UTC),
        datetime.combine(
            day + timedelta(days=1), time.min, tzinfo=_ACADEMY_ZONE
        ).astimezone(UTC),
    )


def evaluate(
    *,
    recognized: bool,
    recent: bool,
    is_exit: bool,
    enabled: bool,
    membership: ValidMembership | None,
    point: str,
    used: int,
) -> DecisionReason:
    if not recognized:
        return "IDENTIDADE_NAO_CONFIRMADA"
    if not recent:
        return "IDENTIFICACAO_FORA_DA_JANELA"
    if is_exit:
        return "SAIDA_PERMITIDA"
    if not enabled:
        return "CLIENTE_INABILITADO"
    if membership is None:
        return "SEM_MATRICULA_VIGENTE"
    if membership.modalidade.strip().casefold() != point.strip().casefold():
        return "MODALIDADE_INCOMPATIVEL"
    limit = membership.limites.limite_acessos
    if limit is not None and used >= limit:
        return "LIMITE_DIARIO"
    return "ENTRADA_PERMITIDA"


def entry_usage(db: Session, client_id: UUID, at: datetime) -> int:
    day_start, day_end = academy_window(at)
    confirmed = (
        db.scalar(
            select(func.count())
            .select_from(AccessEvent)
            .where(
                AccessEvent.cliente_id == client_id,
                AccessEvent.origem == _PASSAGE_ORIGIN,
                AccessEvent.tipo == "PASSAGEM_SIMULADA",
                AccessEvent.direcao == "ENTRADA",
                AccessEvent.ocorrido_em >= day_start,
                AccessEvent.ocorrido_em < day_end,
            )
        )
        or 0
    )
    pending = (
        db.scalar(
            select(func.count())
            .select_from(TurnstileCommand)
            .join(AccessDecision, TurnstileCommand.decisao_id == AccessDecision.id)
            .join(AccessEvent, AccessDecision.evento_id == AccessEvent.id)
            .where(
                AccessEvent.cliente_id == client_id,
                AccessDecision.resultado == "ALLOW",
                AccessDecision.criada_em >= day_start,
                TurnstileCommand.direcao == "ENTRY",
                TurnstileCommand.expira_em > at,
                TurnstileCommand.passagem_evento_id.is_(None),
            )
        )
        or 0
    )
    return confirmed + pending


def prepare_decision(
    db: Session,
    event_id: UUID,
    settings: AccessSettings,
    clock: Callable[[], datetime],
) -> tuple[UUID, bool]:
    identification = db.get(AccessEvent, event_id, with_for_update=True)
    if identification is None or identification.tipo not in {
        "IDENTIFICACAO",
        "IDENTIFICACAO_MANUAL",
    }:
        raise AccessError(404)
    previous = db.scalar(
        select(AccessDecision).where(AccessDecision.evento_id == event_id)
    )
    if previous is not None:
        return previous.id, False

    client = identification.cliente_id
    is_exit = identification.direcao == "SAIDA"
    if client is not None:
        AssignmentDirectory(db).lock_people(client)
    now = clock()
    recent = (
        timedelta()
        <= now - identification.ocorrido_em
        <= timedelta(seconds=settings.access_identification_max_age_seconds)
    )
    enabled = False
    membership = None
    used = 0
    if client is not None and recent and not is_exit:
        enabled = Role.CLIENTE in effective_roles(db, client)
        if enabled:
            membership = valid_membership(db, client, at=now)
        if membership is not None and membership.limites.limite_acessos is not None:
            used = entry_usage(db, client, now)

    reason = evaluate(
        recognized=identification.resultado_identificacao == "IDENTIFICADO"
        and client is not None,
        recent=recent,
        is_exit=is_exit,
        enabled=enabled,
        membership=membership,
        point=settings.access_modalidade_ponto,
        used=used,
    )
    outcome = "ALLOW" if reason in ("ENTRADA_PERMITIDA", "SAIDA_PERMITIDA") else "DENY"
    decision = AccessDecision(
        id=uuid4(),
        evento_id=event_id,
        matricula_id=membership.id if membership else None,
        resultado=outcome,
        motivo=reason,
        criada_em=now,
        regra_json={
            "modalidade_ponto": settings.access_modalidade_ponto,
            "modalidade_contratada": membership.modalidade if membership else None,
            "limite_diario": membership.limites.limite_acessos if membership else None,
            "entradas_e_reservas": used if membership else None,
            "dia_civil": academy_date(now).isoformat(),
        },
    )
    expires_at = now + timedelta(seconds=settings.access_command_ttl_seconds)
    if not is_exit:
        expires_at = min(expires_at, academy_window(now)[1])
    db.add(decision)
    db.flush()
    db.add(
        TurnstileCommand(
            id=uuid4(),
            decisao_id=decision.id,
            request_id=uuid4(),
            direcao="EXIT" if is_exit else "ENTRY",
            expira_em=expires_at,
            estado="CRIADO",
        )
    )
    return decision.id, True


def _command_row(
    db: Session, decision_id: UUID, *, lock: bool = False
) -> TurnstileCommand:
    query = select(TurnstileCommand).where(TurnstileCommand.decisao_id == decision_id)
    if lock:
        query = query.with_for_update()
    return db.scalars(query).one()


def pending_command(db: Session, decision_id: UUID, now: datetime) -> Command | None:
    row = _command_row(db, decision_id)
    if row.estado not in {"CRIADO", "FALHOU"} or now >= row.expira_em:
        return None
    decision = db.get_one(AccessDecision, decision_id)
    event = db.get_one(AccessEvent, decision.evento_id)
    return Command.model_validate(
        {
            "schema_version": 1,
            "request_id": row.request_id,
            "access_decision_id": decision.id,
            "direction": row.direcao,
            "decision": decision.resultado,
            "expires_at": row.expira_em,
            "client_id": event.cliente_id,
        }
    )


def record_delivery(
    db: Session, decision_id: UUID, failure: DeliveryFailure | None
) -> None:
    row = _command_row(db, decision_id, lock=True)
    if row.estado in {"CRIADO", "FALHOU"}:
        row.estado = "ACEITO" if failure is None else "FALHOU"
        row.falha_envio = failure


def view_decision(db: Session, decision_id: UUID, now: datetime) -> DecisionView:
    decision = db.get_one(AccessDecision, decision_id)
    row = _command_row(db, decision_id)
    state = (
        "EXPIRADO"
        if row.estado != "CONFIRMADO" and now >= row.expira_em
        else row.estado
    )
    return DecisionView.model_validate(
        {
            "id": decision.id,
            "evento_id": decision.evento_id,
            "matricula_id": decision.matricula_id,
            "resultado": decision.resultado,
            "motivo": decision.motivo,
            "criada_em": decision.criada_em,
            "regra": decision.regra_json,
            "comando": {
                "request_id": row.request_id,
                "direcao": row.direcao,
                "expira_em": row.expira_em,
                "estado": state,
                "falha_envio": row.falha_envio,
                "passagem_evento_id": row.passagem_evento_id,
            },
        }
    )


def record_passage(
    db: Session, passage: Passage, clock: Callable[[], datetime]
) -> bool:
    key = str(passage.event_id)
    digest = sha256(passage.model_dump_json().encode()).hexdigest()
    db.execute(
        select(func.pg_advisory_xact_lock(func.hashtextextended(f"passagem:{key}", 0)))
    )
    existing = db.scalar(
        select(AccessEvent).where(
            AccessEvent.origem == _PASSAGE_ORIGIN,
            AccessEvent.event_id_externo == key,
        )
    )
    if existing is not None:
        if existing.tipo != "PASSAGEM_SIMULADA" or existing.payload_hash != digest:
            raise AccessError(409)
        return False

    command = db.scalar(
        select(TurnstileCommand).where(
            TurnstileCommand.request_id == passage.request_id
        )
    )
    if command is None:
        raise AccessError(404)
    decision = db.get_one(AccessDecision, command.decisao_id)
    event = db.get_one(AccessEvent, decision.evento_id)
    client = event.cliente_id
    if (
        decision.resultado != "ALLOW"
        or client is None
        or passage.direction != command.direcao
    ):
        raise AccessError(409)
    AssignmentDirectory(db).lock_people(client)
    command = db.get_one(
        TurnstileCommand, command.id, populate_existing=True, with_for_update=True
    )
    if command.passagem_evento_id is not None:
        raise AccessError(409)
    now = clock()
    if now >= command.expira_em or passage.occurred_at >= command.expira_em:
        raise AccessError(410)
    if not decision.criada_em <= passage.occurred_at <= now:
        raise AccessError(409)
    passed = AccessEvent(
        id=uuid4(),
        origem=_PASSAGE_ORIGIN,
        event_id_externo=key,
        cliente_id=client,
        tipo="PASSAGEM_SIMULADA",
        ocorrido_em=passage.occurred_at,
        payload_hash=digest,
        direcao="ENTRADA" if passage.direction == "ENTRY" else "SAIDA",
    )
    db.add(passed)
    db.flush()
    command.passagem_evento_id = passed.id
    command.estado = "CONFIRMADO"
    command.falha_envio = None
    return True

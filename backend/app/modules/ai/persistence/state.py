import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import UUID, uuid4, uuid5

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import digest
from app.events.contracts import AuditEvent
from app.modules.ai.orchestration.settings import Config
from app.modules.ai.persistence.models import (
    EvidenceRecord,
    Execution,
    StageRecord,
    TriageRecord,
)
from app.modules.ai.ports.execution import Context, ExecutionConflict, ProviderError
from app.modules.ai.schemas.execution import (
    Completion,
    Consumption,
    RunRequest,
    RunResult,
    Stage,
)
from app.modules.audit.service import record_audit
from app.modules.identity.service import utc_now
from app.policies.access import Actor

_WORKER = uuid4()


class RateLimited(Exception):
    retry_after = 60


class PostgresState:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        context: Context | None = None,
        base_id: UUID | None = None,
        publisher: Callable[[Session, Actor, Execution, RunResult], UUID] | None = None,
        clock: Callable[[], float] = time.perf_counter,
        now: Callable[[], datetime] = utc_now,
        worker: UUID = _WORKER,
    ) -> None:
        self.sessions, self.context, self.base_id = sessions, context, base_id
        self.publisher, self.clock, self.now, self.worker = (
            publisher,
            clock,
            now,
            worker,
        )

    @staticmethod
    def id(actor: Actor, id: UUID) -> UUID:
        return uuid5(actor.user_id, str(id))

    @staticmethod
    def _serialize(result: RunResult) -> dict[str, object]:
        return result.model_dump(mode="json", exclude={"proposta", "evidencias"})

    def _view(self, session: Session, row: Execution) -> RunResult:
        result = RunResult.model_validate(row.resultado)
        consumption = [
            Consumption.model_validate(stage.dados)
            for stage in session.scalars(
                select(StageRecord)
                .where(StageRecord.execucao_id == row.id)
                .order_by(StageRecord.tipo)
            )
        ]
        return result.model_copy(
            update={
                "consumo": consumption,
                "versao_publicada_id": row.versao_publicada_id,
            }
        )

    @contextmanager
    def _locked(self, actor: Actor, id: UUID) -> Iterator[tuple[Session, Execution]]:
        with self.sessions.begin() as session:
            row = session.get(Execution, self.id(actor, id))
            if row is None or row.ator_id != actor.user_id:
                raise KeyError(id)
            session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:client, 0))"),
                {"client": str(row.cliente_id)},
            )
            row = session.scalar(
                select(Execution)
                .where(Execution.id == row.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            assert row is not None
            yield session, row

    def _terminal(self, row: Execution, result: RunResult) -> None:
        row.estado, row.terminada_em = result.estado, self.now()
        row.resultado = self._serialize(result)

    def _expire(self, session: Session, row: Execution) -> None:
        if row.estado != "EM_EXECUCAO":
            return
        if row.worker_id != self.worker or self.now() >= row.prazo_em:
            result = self._view(session, row).model_copy(
                update={
                    "estado": "TIMEOUT"
                    if self.now() >= row.prazo_em
                    else "INTERROMPIDA",
                    "motivo": "PRAZO_OU_PROCESSO_ENCERRADO",
                }
            )
            self._terminal(row, result)

    def lookup(
        self, actor: Actor, client_id: UUID, request: RunRequest
    ) -> RunResult | None:
        with self.sessions.begin() as session:
            exists = session.get(Execution, self.id(actor, request.solicitacao_id))
        if exists is None:
            return None
        with self._locked(actor, request.solicitacao_id) as (session, row):
            if row.cliente_id != client_id or row.request_hash != digest(
                request.model_dump(mode="json")
            ):
                raise ExecutionConflict()
            self._expire(session, row)
            return self._view(session, row)

    def claim(
        self,
        actor: Actor,
        client_id: UUID,
        request: RunRequest,
        input_hash: str,
        initial: RunResult,
        deadline: float,
    ) -> tuple[bool, RunResult]:
        with self.sessions.begin() as session:
            session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:client, 0))"),
                {"client": str(client_id)},
            )
            old = session.get(Execution, self.id(actor, request.solicitacao_id))
            if old:
                if (
                    old.cliente_id != client_id
                    or old.request_hash != digest(request.model_dump(mode="json"))
                    or old.entrada_hash != input_hash
                ):
                    raise ExecutionConflict()
                self._expire(session, old)
                return False, self._view(session, old)
            now = self.now()
            count = (
                session.scalar(
                    select(func.count())
                    .select_from(Execution)
                    .where(
                        Execution.cliente_id == client_id,
                        Execution.iniciada_em > now - timedelta(seconds=60),
                        Execution.finalidade.in_(["DUVIDA", "ADAPTACAO"]),
                    )
                )
                or 0
            )
            if request.finalidade in {"DUVIDA", "ADAPTACAO"} and count >= 6:
                raise RateLimited()
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise ProviderError("TIMEOUT")
            prep = self.context.preparation if self.context else None
            row = Execution(
                id=self.id(actor, request.solicitacao_id),
                ator_id=actor.user_id,
                cliente_id=client_id,
                idempotency_key=f"{actor.user_id}:{request.solicitacao_id}",
                entrada_hash=input_hash,
                request_hash=digest(request.model_dump(mode="json")),
                finalidade=request.finalidade,
                estado="EM_EXECUCAO",
                onboarding_id=prep.snapshot.id if prep and prep.snapshot else None,
                versao_base_id=self.base_id,
                versao_publicada_id=None,
                config_version=1,
                modelo=initial.modelo,
                prompt_version=initial.versao_prompts,
                iniciada_em=now,
                prazo_em=now + timedelta(seconds=remaining),
                terminada_em=None,
                resultado=self._serialize(initial),
                worker_id=self.worker,
            )
            session.add(row)
            session.flush()
            return True, initial

    def phase(self, actor: Actor, id: UUID, phase: str) -> None:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            if row.estado == "EM_EXECUCAO":
                result = self._view(session, row)
                row.resultado = self._serialize(
                    result.model_copy(update={"etapas": [*result.etapas, phase]})
                )

    def reserve(self, actor: Actor, id: UUID, consumption: Consumption) -> None:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            if (
                row.estado != "EM_EXECUCAO"
                or session.get(StageRecord, uuid5(row.id, consumption.etapa))
                is not None
            ):
                raise ProviderError("ETAPA_ENCERRADA_OU_RESERVADA")
            config = Config.load()
            tokens, _ = config.stage_limits(consumption.etapa)
            allowed = {"CHAT"} if row.finalidade == "DUVIDA" else {"TRIAGEM", "GERACAO"}
            if (
                consumption.etapa not in allowed
                or consumption.chamadas_fisicas != 0
                or consumption.limite_saida_tokens != tokens
                or not 0 < consumption.prompt_bytes <= config.prompt_bytes
            ):
                raise ProviderError("ORCAMENTO_INVALIDO")
            session.add(
                StageRecord(
                    id=uuid5(row.id, consumption.etapa),
                    execucao_id=row.id,
                    tipo=consumption.etapa,
                    estado="RESERVADA",
                    chamadas=0,
                    limite_saida_tokens=tokens,
                    prompt_bytes=consumption.prompt_bytes,
                    prompt_sha256=consumption.prompt_sha256,
                    enviada_em=None,
                    duracao_ms=None,
                    tokens_entrada=None,
                    tokens_saida=None,
                    dados=consumption.model_dump(mode="json"),
                )
            )

    def dispatched(self, actor: Actor, id: UUID, stage: Stage) -> None:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            entry = session.get(StageRecord, uuid5(row.id, stage))
            if row.estado != "EM_EXECUCAO" or entry is None or entry.chamadas:
                raise ProviderError("DESPACHO_RECUSADO")
            consumption = Consumption.model_validate(entry.dados).model_copy(
                update={"chamadas_fisicas": 1}
            )
            entry.enviada_em = self.now()
            entry.chamadas, entry.estado, entry.dados = (
                1,
                "ENVIADA",
                consumption.model_dump(mode="json"),
            )

    def usage(
        self, actor: Actor, id: UUID, stage: Stage, completion: Completion
    ) -> None:
        with self._locked(actor, id) as (session, row):
            entry = session.get(StageRecord, uuid5(row.id, stage))
            if entry is None or entry.chamadas != 1:
                raise ProviderError("CONSUMO_SEM_DESPACHO")
            consumption = Consumption.model_validate(entry.dados).model_copy(
                update={
                    "uso": completion.usage,
                    "consumo_desconhecido": completion.usage is None,
                }
            )
            entry.dados, entry.estado = consumption.model_dump(mode="json"), "RECEBIDA"
            if entry.enviada_em:
                entry.duracao_ms = max(
                    0, int((self.now() - entry.enviada_em).total_seconds() * 1000)
                )
            if completion.usage:
                entry.tokens_entrada, entry.tokens_saida = (
                    completion.usage.prompt_tokens,
                    completion.usage.completion_tokens,
                )

    def active(self, actor: Actor, id: UUID, now: float) -> bool:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            return row.estado == "EM_EXECUCAO"

    def finish(self, actor: Actor, id: UUID, result: RunResult) -> RunResult:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            terminal = row.estado != "EM_EXECUCAO"
            if terminal:
                ended = self._view(session, row)
                result = ended.model_copy(
                    update={
                        "triagem": result.triagem or ended.triagem,
                        "evidencias": result.evidencias,
                    }
                )
            if not terminal and result.proposta and self.publisher:
                # Savepoint impede publicação parcial, preservando o recibo de falha.
                try:
                    with session.begin_nested():
                        published = self.publisher(session, actor, row, result)
                        if self.now() >= row.prazo_em:
                            raise PublicationRejected("PRAZO_PUBLICACAO_EXCEDIDO")
                    row.versao_publicada_id = published
                    result = result.model_copy(
                        update={
                            "estado": "PUBLICADA",
                            "versao_publicada_id": published,
                            "proposta": None,
                        }
                    )
                except PublicationRejected as error:
                    result = result.model_copy(
                        update={
                            "estado": "TIMEOUT"
                            if error.code == "PRAZO_PUBLICACAO_EXCEDIDO"
                            else "INTERROMPIDA",
                            "motivo": error.code,
                            "proposta": None,
                        }
                    )
            elif not terminal and result.proposta:
                result = result.model_copy(
                    update={
                        "estado": "FALHA",
                        "motivo": "PUBLICADOR_AUSENTE",
                        "proposta": None,
                    }
                )
            if result.triagem and result.triagem.snapshot:
                triage = result.triagem
                assert triage.snapshot is not None
                triage_id = uuid5(row.id, "triagem")
                stored_triage = session.get(TriageRecord, triage_id)
                if stored_triage:
                    stored_triage.resumo = triage.model_dump(mode="json")
                    stored_triage.estado = triage.estado
                    stored_triage.motivos = list(triage.motivos)
                else:
                    session.add(
                        TriageRecord(
                            id=uuid5(row.id, "triagem"),
                            execucao_id=row.id,
                            onboarding_id=triage.snapshot.id,
                            resumo=triage.model_dump(mode="json"),
                            regra_version=triage.regra_versao,
                            estado=triage.estado,
                            motivos=list(triage.motivos),
                        )
                    )
            for evidence in result.evidencias:
                if (
                    session.get(
                        EvidenceRecord, uuid5(row.id, str(evidence.fragmento_id))
                    )
                    is not None
                ):
                    continue
                session.add(
                    EvidenceRecord(
                        id=uuid5(row.id, str(evidence.fragmento_id)),
                        execucao_id=row.id,
                        fragmento_id=evidence.fragmento_id,
                        finalidade=row.finalidade,
                        metadados=evidence.model_dump(mode="json", exclude={"texto"}),
                    )
                )
            if terminal:
                row.resultado = self._serialize(result)
            else:
                self._terminal(row, result.model_copy(update={"proposta": None}))
            record_audit(
                session,
                AuditEvent(
                    id=uuid5(row.id, "finished"),
                    actor_id=actor.user_id,
                    action="ai.execution.finished",
                    resource_type="execucao_ia",
                    resource_id=row.id,
                    reason_code=result.estado.lower(),
                    correlation_id=id,
                    occurred_at=self.now(),
                ),
            )
            session.flush()
            return self._view(session, row)

    def cancel(self, actor: Actor, id: UUID) -> RunResult:
        with self._locked(actor, id) as (session, row):
            self._expire(session, row)
            if row.estado == "EM_EXECUCAO":
                self._terminal(
                    row,
                    self._view(session, row).model_copy(
                        update={
                            "estado": "CANCELADA",
                            "motivo": "CANCELAMENTO_SOLICITADO",
                            "resposta": None,
                            "proposta": None,
                        }
                    ),
                )
            return self._view(session, row)


class PublicationRejected(Exception):
    def __init__(self, code: str) -> None:
        self.code = code

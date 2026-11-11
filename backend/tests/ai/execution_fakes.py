"""Estado volátil de referência APENAS para testes; AI-03 fornecerá persistência."""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from app.modules.ai.ports.execution import Context, ExecutionConflict
from app.modules.ai.schemas.execution import (
    Completion,
    Consumption,
    RunRequest,
    RunResult,
    Stage,
)
from app.modules.knowledge.retrieval.contracts import Evidence, Result, Scope
from app.modules.knowledge.schemas import Purpose
from app.policies.access import Actor


@dataclass
class Record:
    client: UUID
    input_hash: str
    deadline: float
    result: RunResult


class MemoryState:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, UUID], Record] = {}
        self.lock = threading.RLock()

    def record(self, actor: Actor, id: UUID) -> Record:
        return self.records[actor.user_id, id]

    def claim(
        self,
        actor: Actor,
        client_id: UUID,
        request: RunRequest,
        input_hash: str,
        initial: RunResult,
        deadline: float,
    ) -> tuple[bool, RunResult]:
        with self.lock:
            key = (actor.user_id, request.solicitacao_id)
            old = self.records.get(key)
            if old:
                if old.client != client_id or old.input_hash != input_hash:
                    raise ExecutionConflict()
                return False, old.result.model_copy(deep=True)
            self.records[key] = Record(
                client_id, input_hash, deadline, initial.model_copy(deep=True)
            )
            return True, initial

    def phase(self, actor: Actor, id: UUID, phase: str) -> None:
        with self.lock:
            record = self.record(actor, id)
            if record.result.estado == "EM_EXECUCAO":
                record.result = record.result.model_copy(
                    update={"etapas": [*record.result.etapas, phase]}
                )

    def reserve(self, actor: Actor, id: UUID, consumption: Consumption) -> None:
        with self.lock:
            record = self.record(actor, id)
            if record.result.estado != "EM_EXECUCAO" or any(
                c.etapa == consumption.etapa for c in record.result.consumo
            ):
                raise ExecutionConflict()
            record.result = record.result.model_copy(
                update={"consumo": [*record.result.consumo, consumption]}
            )

    def dispatched(self, actor: Actor, id: UUID, stage: Stage) -> None:
        with self.lock:
            record = self.record(actor, id)
            if record.result.estado != "EM_EXECUCAO":
                raise ExecutionConflict()
            updated = []
            for c in record.result.consumo:
                if c.etapa == stage:
                    if c.chamadas_fisicas != 0:
                        raise ExecutionConflict()
                    c = c.model_copy(update={"chamadas_fisicas": 1})
                updated.append(c)
            record.result = record.result.model_copy(update={"consumo": updated})

    def usage(
        self, actor: Actor, id: UUID, stage: Stage, completion: Completion
    ) -> None:
        with self.lock:
            record = self.record(actor, id)
            record.result = record.result.model_copy(
                update={
                    "consumo": [
                        c.model_copy(
                            update={
                                "uso": completion.usage,
                                "consumo_desconhecido": completion.usage is None,
                            }
                        )
                        if c.etapa == stage
                        else c
                        for c in record.result.consumo
                    ]
                }
            )

    def active(self, actor: Actor, id: UUID, now: float) -> bool:
        with self.lock:
            record = self.record(actor, id)
            return record.result.estado == "EM_EXECUCAO" and now < record.deadline

    def finish(self, actor: Actor, id: UUID, result: RunResult) -> RunResult:
        with self.lock:
            record = self.record(actor, id)
            if record.result.estado == "EM_EXECUCAO":
                record.result = result.model_copy(
                    update={"consumo": record.result.consumo}
                )
            return record.result.model_copy(deep=True)

    def cancel(self, actor: Actor, id: UUID) -> RunResult:
        with self.lock:
            record = self.record(actor, id)
            if record.result.estado == "EM_EXECUCAO":
                record.result = record.result.model_copy(
                    update={
                        "estado": "CANCELADA",
                        "motivo": "CANCELAMENTO_SOLICITADO",
                        "proposta": None,
                        "resposta": None,
                    }
                )
            return record.result.model_copy(deep=True)


class Contexts:
    def __init__(self, context: Context) -> None:
        self.context, self.valid = context, True

    def resolve(self, actor: Actor, client_id: UUID, request: RunRequest) -> Context:
        return self.context

    def current(self, actor: Actor, context: Context, request: RunRequest) -> bool:
        return self.valid


class Sources:
    def __init__(self, evidence: Evidence) -> None:
        self.package = Result(
            estado="EVIDENCIAS_ENCONTRADAS",
            evidencias=[evidence],
            suporte_saude="NAO_SOLICITADO",
            motivo="OK",
        )
        self.valid = True
        self.queries: list[tuple[UUID, Purpose, str, Scope | None]] = []

    def retrieve(
        self, context: Context, purpose: Purpose, query: str, scope: Scope | None = None
    ) -> Result:
        self.queries.append((context.client_id, purpose, query, scope))
        return self.package

    def current(self, evidences: tuple[Evidence, ...]) -> bool:
        return self.valid


class Model:
    def __init__(
        self, responses: list[str | Exception], hook: Callable[[], None] = lambda: None
    ) -> None:
        self.responses, self.hook = responses, hook
        self.calls: list[Stage] = []
        self.messages: list[list[dict[str, str]]] = []

    def complete(
        self,
        messages: list[dict[str, str]],
        stage: Stage,
        output_tokens: int,
        timeout: float,
        on_dispatch: Callable[[], None],
    ) -> Completion:
        on_dispatch()
        self.calls.append(stage)
        self.messages.append(messages)
        self.hook()
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return Completion(content=response)

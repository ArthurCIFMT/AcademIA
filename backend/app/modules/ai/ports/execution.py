from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.ai.schemas.execution import (
    Completion,
    Consumption,
    PlanAnswer,
    RunRequest,
    RunResult,
    Stage,
)
from app.modules.ai.triage.contracts import TriageResult
from app.modules.knowledge.retrieval.contracts import Evidence, Result, Scope
from app.modules.knowledge.schemas import Purpose
from app.modules.training.schemas import ExerciseCandidate
from app.policies.access import Actor


@dataclass(frozen=True)
class Context:
    actor_id: UUID
    client_id: UUID
    fingerprint: str
    preparation: TriageResult | None = None
    candidates: tuple[ExerciseCandidate, ...] = ()
    health_scope: Scope | None = None
    forbidden_ids: frozenset[UUID] = frozenset()
    base_version_id: UUID | None = None
    base_plan: PlanAnswer | None = None


class ContextPort(Protocol):
    def resolve(
        self, actor: Actor, client_id: UUID, request: RunRequest
    ) -> Context: ...
    def current(self, actor: Actor, context: Context, request: RunRequest) -> bool: ...


class EvidencePort(Protocol):
    def retrieve(
        self, context: Context, purpose: Purpose, query: str, scope: Scope | None = None
    ) -> Result: ...
    def current(self, evidences: tuple[Evidence, ...]) -> bool: ...


class LLMPort(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        stage: Stage,
        output_tokens: int,
        timeout: float,
        on_dispatch: Callable[[], None],
    ) -> Completion: ...


class StatePort(Protocol):
    def claim(
        self,
        actor: Actor,
        client_id: UUID,
        request: RunRequest,
        input_hash: str,
        initial: RunResult,
        deadline: float,
    ) -> tuple[bool, RunResult]: ...
    def phase(self, actor: Actor, id: UUID, phase: str) -> None: ...
    def reserve(self, actor: Actor, id: UUID, consumption: Consumption) -> None: ...
    def dispatched(self, actor: Actor, id: UUID, stage: Stage) -> None: ...
    def usage(
        self, actor: Actor, id: UUID, stage: Stage, completion: Completion
    ) -> None: ...
    def active(self, actor: Actor, id: UUID, now: float) -> bool: ...
    def finish(self, actor: Actor, id: UUID, result: RunResult) -> RunResult: ...
    def cancel(self, actor: Actor, id: UUID) -> RunResult: ...


class ExecutionConflict(Exception):
    pass


class ContextDenied(Exception):
    pass


class ProviderError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

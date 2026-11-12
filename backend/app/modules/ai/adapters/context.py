from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import digest
from app.modules.ai.ports.execution import Context, ContextDenied
from app.modules.ai.schemas.execution import PlanAnswer, PlanOutline, RunRequest
from app.modules.ai.triage.service import TriagePermissionError, TriageService
from app.modules.assignments.service import PostgresAssignmentReader
from app.modules.identity.roles import effective_roles
from app.modules.knowledge.retrieval.contracts import Scope
from app.modules.training.catalog import eligible_exercises
from app.policies.access import Actor, Operation, allows


class PostgresContext:
    """Somente serviços públicos dos módulos; nenhuma chamada LLM em transação."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        base_reader: Callable[[Actor, UUID, UUID], PlanAnswer | PlanOutline | None]
        | None = None,
        scope_resolver: Callable[[UUID], Scope | None] | None = None,
    ) -> None:
        self.sessions = sessions
        self.base_reader, self.scope_resolver = base_reader, scope_resolver

    def resolve(self, actor: Actor, client_id: UUID, request: RunRequest) -> Context:
        with self.sessions.begin() as session:
            fresh = Actor(actor.user_id, effective_roles(session, actor.user_id))
            operation = Operation.USE_AI_CONTEXT
            if request.finalidade != "DUVIDA" and actor.user_id != client_id:
                operation = Operation.PRESCRIBE_WORKOUT
            if not allows(
                fresh,
                operation,
                client_id=client_id,
                assignments=PostgresAssignmentReader(session),
            ):
                raise ContextDenied()
        if request.finalidade == "DUVIDA":
            return Context(
                actor.user_id,
                client_id,
                digest(
                    {
                        "actor": str(actor.user_id),
                        "client": str(client_id),
                        "roles": sorted(fresh.roles),
                    }
                ),
            )
        try:
            preparation = TriageService(self.sessions).evaluate(fresh, client_id)
        except TriagePermissionError:
            raise ContextDenied() from None
        if request.finalidade == "ADAPTACAO" and (
            not preparation.snapshot
            or preparation.snapshot.id != request.onboarding_confirmado_id
        ):
            raise ContextDenied()
        with self.sessions.begin() as session:
            candidates = tuple(eligible_exercises(session))
        if (
            digest([c.model_dump(mode="json") for c in candidates])
            != preparation.recursos_sha256
        ):
            raise ContextDenied()
        base = (
            self.base_reader(fresh, client_id, request.versao_base_id)
            if self.base_reader and request.versao_base_id
            else None
        )
        scope = self.scope_resolver(client_id) if self.scope_resolver else None
        fingerprint = digest(
            {
                "preparation": preparation.model_dump(mode="json"),
                "candidates": [c.model_dump(mode="json") for c in candidates],
                "base": base.model_dump(mode="json") if base else None,
                "scope": scope.model_dump(mode="json") if scope else None,
                "roles": sorted(fresh.roles),
            }
        )
        return Context(
            actor.user_id,
            client_id,
            fingerprint,
            preparation,
            candidates,
            scope,
            base_version_id=request.versao_base_id,
            base_plan=base,
        )

    def current(self, actor: Actor, context: Context, request: RunRequest) -> bool:
        try:
            return (
                self.resolve(actor, context.client_id, request).fingerprint
                == context.fingerprint
            )
        except (ContextDenied, TriagePermissionError):
            return False

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import digest
from app.events.contracts import AuditEvent
from app.modules.ai.triage.contracts import SnapshotRef, TriageResult
from app.modules.ai.triage.engine import Engine
from app.modules.assignments.service import PostgresAssignmentReader
from app.modules.audit.service import record_audit
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.knowledge.retrieval.contracts import Evidence
from app.modules.onboarding.schemas import SnapshotView
from app.modules.onboarding.service import get_current_snapshot
from app.modules.people.onboarding_directory import lock_onboarding_client
from app.modules.training.catalog import eligible_exercises
from app.policies.access import Actor, Operation, allows


class TriagePermissionError(Exception):
    pass


@dataclass(frozen=True)
class Context:
    snapshot: SnapshotView | None
    candidates: int
    resources_hash: str

    @property
    def reference(self) -> SnapshotRef | None:
        if self.snapshot is None:
            return None
        return SnapshotRef(
            id=self.snapshot.id,
            numero=self.snapshot.numero,
            revisao=self.snapshot.revisao,
        )


class TriageService:
    def __init__(
        self, sessions: sessionmaker[Session], engine: Engine | None = None
    ) -> None:
        self.sessions, self.engine = sessions, engine or Engine()

    def _context(self, session: Session, actor: Actor, client_id: UUID) -> Context:
        current = Actor(actor.user_id, effective_roles(session, actor.user_id))
        if (
            not allows(
                current,
                Operation.READ_HEALTH,
                client_id=client_id,
                assignments=PostgresAssignmentReader(session),
            )
            or lock_onboarding_client(session, client_id) is None
        ):
            raise TriagePermissionError()
        snapshot = get_current_snapshot(session, client_id)
        candidates = eligible_exercises(session)
        return Context(
            snapshot,
            len(candidates),
            digest([c.model_dump(mode="json") for c in candidates]),
        )

    def evaluate(
        self, actor: Actor, client_id: UUID, *, evidences: tuple[Evidence, ...] = ()
    ) -> TriageResult:
        with self.sessions.begin() as session:
            context = self._context(session, actor, client_id)
        snapshot = context.snapshot
        result = self.engine.evaluate(
            snapshot=context.reference,
            completed=snapshot is not None,
            age=snapshot.idade_snapshot if snapshot else None,
            data=snapshot.dados.model_dump(mode="json") if snapshot else None,
            candidates=context.candidates,
            resources_hash=context.resources_hash,
            evidences=evidences,
        )
        # Fora da transação: a análise não retém locks ou conexões SQL.
        with self.sessions.begin() as session:
            current = self._context(session, actor, client_id)
            if current.reference != context.reference:
                result = result.model_copy(
                    update={
                        "estado": "DADOS_INSUFICIENTES",
                        "estado_tecnico": "CONCLUIDA",
                        "motivos": ["CONTEXTO_SUPERADO"],
                        "resumo": None,
                        "resumo_sha256": None,
                        "evidencias_ids": [],
                        "geracao_permitida": False,
                    }
                )
            elif current.resources_hash != context.resources_hash:
                result = result.model_copy(
                    update={
                        "motivos": [*result.motivos, "RECURSOS_ALTERADOS"],
                        "exercicios_elegiveis": current.candidates,
                        "recursos_sha256": current.resources_hash,
                        "geracao_permitida": False,
                    }
                )
            record_audit(
                session,
                AuditEvent(
                    id=uuid4(),
                    actor_id=actor.user_id,
                    action="ai.triage.checked",
                    resource_type="onboarding" if context.reference else "cliente",
                    resource_id=context.reference.id
                    if context.reference
                    else client_id,
                    reason_code=f"policy_v{self.engine.policy.version}",
                    correlation_id=uuid4(),
                    occurred_at=utc_now(),
                ),
            )
            return result

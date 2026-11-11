import time
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import digest
from app.contracts.training.generated import ValidatedGeneration
from app.modules.ai.adapters.context import PostgresContext
from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.orchestration.service import Orchestrator
from app.modules.ai.orchestration.settings import Config
from app.modules.ai.orchestration.validation import validate_plan
from app.modules.ai.persistence.models import Execution
from app.modules.ai.persistence.state import PostgresState, PublicationRejected
from app.modules.ai.policies.triage import Policy
from app.modules.ai.ports.execution import Context, ContextDenied, EvidencePort, LLMPort
from app.modules.ai.schemas.execution import RunRequest, RunResult
from app.modules.knowledge.embeddings.encoder import EmbeddingError
from app.modules.knowledge.embeddings.runtime import get_encoder
from app.modules.knowledge.retrieval.contracts import Evidence, Result, Scope
from app.modules.knowledge.retrieval.publication import lock_publication_evidence
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Purpose
from app.modules.knowledge.vector.contracts import VectorError
from app.modules.knowledge.vector.runtime import get_vector_store
from app.modules.onboarding.service import get_current_snapshot
from app.modules.training.catalog import eligible_exercises
from app.modules.training.generated import (
    current_generation_base,
    lock_generation_client,
    publish_generated,
)
from app.modules.training.publication import send_review_notice
from app.modules.training.workout_schemas import (
    WorkoutContent,
    WorkoutDayInput,
    WorkoutItemInput,
)
from app.modules.training.workouts import WorkoutError
from app.policies.access import Actor


class GenerationService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        llm: LLMPort | None = None,
        evidence: EvidencePort | None = None,
        contexts: PostgresContext | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.sessions, self.llm, self.evidence = sessions, llm, evidence
        self.contexts, self.clock = contexts or PostgresContext(sessions), clock

    def authorize(self, actor: Actor, client_id: UUID) -> None:
        with self.sessions.begin() as session:
            try:
                lock_generation_client(session, actor, client_id)
            except WorkoutError:
                raise ContextDenied() from None

    def _publisher(
        self, context: Context
    ) -> Callable[[Session, Actor, Execution, RunResult], UUID]:
        def publish(
            session: Session, actor: Actor, row: Execution, result: RunResult
        ) -> UUID:
            try:
                lock_generation_client(session, actor, row.cliente_id)
                snapshot = get_current_snapshot(session, row.cliente_id)
                triage = result.triagem
                if (
                    not triage
                    or not triage.geracao_permitida
                    or not triage.snapshot
                    or not snapshot
                    or snapshot.id != triage.snapshot.id
                    or snapshot.revisao != triage.snapshot.revisao
                    or triage.regra_sha256 != Policy().fingerprint
                    or not result.proposta
                ):
                    raise PublicationRejected("CONTEXTO_TRIAGEM_SUPERADO")
                candidates = tuple(eligible_exercises(session))
                if (
                    digest([c.model_dump(mode="json") for c in candidates])
                    != triage.recursos_sha256
                ):
                    raise PublicationRejected("RECURSOS_SUPERADOS")
                validate_plan(result.proposta, context, tuple(result.evidencias))
                if not lock_publication_evidence(session, tuple(result.evidencias)):
                    raise PublicationRejected("FONTES_SUPERADAS")
                plan = result.proposta
                content = WorkoutContent(
                    onboarding_id=snapshot.id,
                    dias=[
                        WorkoutDayInput(
                            titulo=day.titulo,
                            itens=[
                                WorkoutItemInput.model_validate(
                                    item.model_dump(exclude={"ordem"})
                                )
                                for item in day.itens
                            ],
                        )
                        for day in plan.dias
                    ],
                )
                return publish_generated(
                    session,
                    actor,
                    row.cliente_id,
                    ValidatedGeneration(
                        row.id, content, row.versao_base_id, plan.explicacao
                    ),
                )
            except WorkoutError:
                raise PublicationRejected("PUBLICACAO_REVALIDACAO_RECUSADA") from None
            except ValueError:
                raise PublicationRejected("PUBLICACAO_CONTRATO_INVALIDO") from None

        return publish

    def generate(self, actor: Actor, client_id: UUID, request: RunRequest) -> RunResult:
        if request.finalidade != "GERACAO":
            raise ValueError(
                "Esta entrega expõe somente geração; chat/adaptação em AI-05."
            )
        self.authorize(actor, client_id)
        existing = PostgresState(self.sessions, clock=self.clock).lookup(
            actor, client_id, request
        )
        if existing is not None:
            return existing
        context = self.contexts.resolve(actor, client_id, request)
        with self.sessions.begin() as session:
            base_id = current_generation_base(session, actor, client_id)
        state = PostgresState(
            self.sessions,
            context=context,
            base_id=base_id,
            publisher=self._publisher(context),
            clock=self.clock,
        )
        config = Config.load()
        owned_llm = None
        # Carregamento lazy: casos bloqueados não precisam de pesos/chave/corpus.
        service = self

        class FixedContext:
            def resolve(
                self, actor: Actor, client_id: UUID, request: RunRequest
            ) -> Context:
                return context

            def current(
                self, actor: Actor, value: Context, request: RunRequest
            ) -> bool:
                return service.contexts.current(actor, value, request)

        class LazyEvidence:
            def retrieve(
                self,
                context: Context,
                purpose: Purpose,
                query: str,
                scope: Scope | None = None,
            ) -> Result:
                try:
                    if service.evidence is None:
                        store = get_vector_store()
                        service.evidence = RagEvidence(
                            Retriever(service.sessions, store, get_encoder()),
                            service.sessions,
                            store.check,
                        )
                    return service.evidence.retrieve(context, purpose, query, scope)
                except (EmbeddingError, VectorError, OSError):
                    return Result(
                        estado="SERVICO_INDISPONIVEL",
                        evidencias=[],
                        suporte_saude="NAO_VERIFICADO",
                        motivo="RAG_INDISPONIVEL",
                    )

            def current(self, evidences: tuple[Evidence, ...]) -> bool:
                return (
                    service.evidence.current(evidences)
                    if service.evidence
                    else not evidences
                )

        if self.llm is None:
            owned_llm = GroqAdapter(config)
        runtime_llm = self.llm or owned_llm
        assert runtime_llm is not None
        try:
            result = Orchestrator(
                FixedContext(),
                LazyEvidence(),
                runtime_llm,
                state,
                config=config,
                clock=self.clock,
            ).execute(actor, client_id, request)
            if result.estado == "PUBLICADA" and result.versao_publicada_id:
                try:
                    send_review_notice(
                        self.sessions,
                        actor,
                        client_id,
                        result.versao_publicada_id,
                        generated_request=True,
                    )
                except WorkoutError:
                    pass  # Designação mudou; publicação e fila já estão persistidas.
            return result
        finally:
            if owned_llm:
                owned_llm.close()

    def status(self, actor: Actor, id: UUID) -> RunResult:
        with self.sessions.begin() as session:
            owner = session.get(Execution, PostgresState.id(actor, id))
            if owner is None:
                raise KeyError(id)
            client_id = owner.cliente_id
        self.authorize(actor, client_id)
        state = PostgresState(self.sessions)
        with state._locked(actor, id) as (session, row):
            state._expire(session, row)
            return state._view(session, row)

    def cancel(self, actor: Actor, id: UUID) -> RunResult:
        self.status(actor, id)
        return PostgresState(self.sessions).cancel(actor, id)

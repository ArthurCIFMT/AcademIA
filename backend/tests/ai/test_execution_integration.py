import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.context import PostgresContext
from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.orchestration.service import Orchestrator
from app.modules.ai.ports.execution import Context, ContextDenied
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.equipment.models import Equipment
from app.modules.knowledge.ingestion.indexing import Indexer
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Decision
from app.modules.knowledge.service import decide
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from tests.ai.execution_fakes import MemoryState, Model, Sources
from tests.ai.test_execution import evidence, request
from tests.ai.test_triage_integration import complete, exercise, seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions
from tests.knowledge.test_indexing import setup
from tests.knowledge.test_retrieval import QueryDouble


@pytest.mark.integration
def test_fresh_authorization_own_chat_and_assigned_instructor(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    port = PostgresContext(sessions)
    req = request("DUVIDA")
    context = port.resolve(people["cliente"], people["cliente"].user_id, req)
    assert context.preparation is None  # Não exige onboarding.
    for name in ["outro", "admin", "atendente", "instrutor"]:
        with pytest.raises(ContextDenied):
            port.resolve(people[name], people["cliente"].user_id, req)
    complete(sessions, people["cliente"])
    exercise(sessions, people["admin"])
    with sessions.begin() as session:
        change_assignment(
            session,
            people["cliente"].user_id,
            ChangeAssignment(instrutor_id=people["instrutor"].user_id, vigente_id=None),
            people["admin"],
            uuid4(),
        )
    assert port.resolve(
        people["instrutor"], people["cliente"].user_id, request()
    ).candidates
    with pytest.raises(ContextDenied):
        port.resolve(people["instrutor"], people["cliente"].user_id, req)


@pytest.mark.integration
def test_catalog_change_during_generation_cannot_release_proposal(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    complete(sessions, people["cliente"])
    exercise(sessions, people["admin"], equipment=True)
    contexts = PostgresContext(sessions)
    sources = Sources(evidence())
    state = MemoryState()

    def change() -> None:
        with sessions.begin() as session:
            item = session.scalar(select(Equipment))
            assert item is not None
            item.operacional = False
            item.revision += 1

    llm = Model(
        [
            json.dumps(
                {
                    "alerta_grave": False,
                    "lacuna": False,
                    "atualizacao_onboarding_necessaria": False,
                }
            )
        ],
        change,
    )
    result = Orchestrator(contexts, sources, llm, state).execute(
        people["cliente"], people["cliente"].user_id, request()
    )
    assert result.estado == "INTERROMPIDA" and result.proposta is None
    assert llm.calls == ["TRIAGEM"] and result.consumo[0].chamadas_fisicas == 1


@pytest.mark.integration
def test_real_rag_bridge_revocation_before_delivery(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, storage, ref, extraction, selection = setup(sessions, tmp_path)
    encoder = QueryDouble()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        Indexer(sessions, store, encoder, lock_root=tmp_path / "locks").run(
            actor, extraction, selection
        )
        bridge = RagEvidence(Retriever(sessions, store, encoder), sessions, store.check)
        context = Context(actor.user_id, actor.user_id, "test")
        package = bridge.retrieve(
            context, "DUVIDAS", "Quais os cuidados nos exercícios?"
        )
        assert package.estado == "EVIDENCIAS_ENCONTRADAS"
        assert bridge.current(tuple(package.evidencias))
        with sessions.begin() as session:
            decide(
                session,
                actor,
                ref.version_id,
                Decision(revisao=2, estado="REVOGADO", motivo="Teste sintético"),
                storage,
                uuid4(),
            )
        assert not bridge.current(tuple(package.evidencias))
    finally:
        store.close()

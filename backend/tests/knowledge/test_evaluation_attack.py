import os
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.ports.execution import Context
from app.modules.knowledge.embeddings.encoder import E5Encoder
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from tests.ai.evaluation.live_support import attack_source, initial_literature
from tests.ai.test_triage_integration import seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1",
    reason="Este ensaio exige E5 real, sem substituição por double.",
)
def test_real_attack_fixture_reaches_retrieval_without_provider(
    sessions: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    people = seed(sessions)
    encoder = E5Encoder()
    storage = CorpusStorage(tmp_path / "corpus")
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        initial_literature(sessions, people["admin"], storage, encoder, store, tmp_path)
        attack_source(sessions, people["admin"], storage, encoder, store, tmp_path)
        port = RagEvidence(Retriever(sessions, store, encoder), sessions, store.check)
        actor = people["cliente"]
        result = port.retrieve(
            Context(actor.user_id, actor.user_id, "fixture"),
            "DUVIDAS",
            "Qual a definição de volume de treino em séries e repetições?",
        )
        assert result.estado == "EVIDENCIAS_ENCONTRADAS"
        assert any("INSTRUÇÃO MALICIOSA DE TESTE" in e.texto for e in result.evidencias)
        assert port.current(tuple(result.evidencias))
    finally:
        encoder.close()
        store.close()

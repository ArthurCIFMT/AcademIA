import hashlib
import json
import os
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.ports.execution import Context
from app.modules.knowledge.embeddings.encoder import E5Encoder
from app.modules.knowledge.ingestion.contracts import ExtractionPolicy
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Purpose
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from app.modules.onboarding.schemas import DraftData
from app.modules.training.catalog import eligible_exercises
from tests.ai.evaluation.fixtures import catalog_fixture, profile_data
from tests.ai.evaluation.live_support import initial_literature
from tests.ai.evaluation.reporting import ROOT, load_dataset, write_json
from tests.ai.test_triage import CASES
from tests.ai.test_triage_integration import seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


def test_profiles_preserve_unknowns_and_realistic_differences() -> None:
    data = load_dataset()
    profiles = [DraftData.model_validate(p["dados"]) for p in data["perfis"].values()]
    assert len(profiles) == 8
    assert (
        len(
            {
                (p.objetivo_principal, p.dias_semana, p.duracao_sessao_min)
                for p in profiles
            }
        )
        >= 5
    )
    for case in data["real"]:
        if case["rota"] != "DUVIDA" and case["origem"] != "triagem:T02":
            DraftData.model_validate(profile_data(case, data, CASES))
    assert (
        data["perfis"]["saude-desconhecida"]["dados"]["possui_condicoes_saude"]
        == "NAO_SEI"
    )
    assert data["real"][-3]["esperado"] == "DADOS_INSUFICIENTES"


def test_selection_matches_original_and_requires_completed_extraction() -> None:
    selection = json.loads(
        (ROOT / "docs/testes/ai06-corpus-v1.json").read_text("utf-8")
    )
    catalog = json.loads((ROOT / "materiais/rag/catalogo.json").read_text("utf-8-sig"))
    approved = json.loads(
        (ROOT / "materiais/rag/corpus-inicial.json").read_text("utf-8")
    )
    for entry in selection["documentos"]:
        source = next(d for d in catalog["documentos"] if d["id"] == entry["fonte_id"])
        allowed = next(d for d in approved["documentos"] if d["id"] == source["id"])
        body = (ROOT / "materiais/rag" / source["arquivo"]).read_bytes()
        assert source["aprovado_para_rag"]
        assert (
            hashlib.sha256(body).hexdigest()
            == entry["arquivo_sha256"]
            == allowed["sha256"]
        )
        assert set(entry["finalidades"]) <= set(allowed["finalidades"])
        result = parse(body, "PDF", None, ExtractionPolicy())
        assert result.estado == "CONCLUIDA"
        for span in entry["trechos"]:
            page = next(p for p in result.paginas if p.numero == span["pagina"])
            text = page.texto[span["inicio"] : span["fim"]]
            assert text.strip() and page.situacao == "TEXTO"
            assert hashlib.sha256(text.encode()).hexdigest() == span["texto_hash"]


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1", reason="Requer E5 real."
)
def test_supplement_reaches_triage_and_generation_without_llm(
    sessions: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    people = seed(sessions)
    catalog_fixture(sessions, people["admin"])
    with sessions.begin() as session:
        viable = eligible_exercises(session)
        assert len(viable) == 6
        assert all(c.nome != "Leg press" for c in viable)
        assert any(any(group) for c in viable for group in c.combinacoes_disponiveis)
    encoder = E5Encoder()
    storage = CorpusStorage(tmp_path / "corpus")
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        encoder.queries(["Inicialização"], 90)
        initial_literature(sessions, people["admin"], storage, encoder, store, tmp_path)
        port = RagEvidence(Retriever(sessions, store, encoder), sessions, store.check)
        actor = people["cliente"]
        rows = []
        queries: list[tuple[Purpose, str]] = [
            (
                "TRIAGEM",
                "Cuidados e restrições para atividade física: "
                '{"condicoes":[],"limitacoes":[],"medicacoes":[],"observacoes":""}',
            ),
            (
                "GERACAO_GERAL",
                "Treinamento para FORCA; experiência INICIANTE; "
                '{"condicoes":[],"limitacoes":[],"medicacoes":[],"observacoes":""}',
            ),
            (
                "GERACAO_GERAL",
                "Treinamento para HIPERTROFIA; experiência INTERMEDIARIO; "
                '{"condicoes":[],"limitacoes":[],"medicacoes":[],"observacoes":""}',
            ),
        ]
        for purpose, query in queries:
            result = port.retrieve(
                Context(actor.user_id, actor.user_id, "fixture"), purpose, query
            )
            rows.append(
                {
                    "finalidade": purpose,
                    "estado": result.estado,
                    "scores": [e.score for e in result.evidencias],
                }
            )
            assert result.estado == "EVIDENCIAS_ENCONTRADAS", rows
            assert port.current(tuple(result.evidencias))
        report = os.environ.get("ACADEMIA_AI_CORPUS_REPORT")
        if report:
            write_json(Path(report), {"sem_llm": True, "consultas": rows})
    finally:
        encoder.close()
        store.close()

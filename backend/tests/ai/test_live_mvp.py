"""Regressão opt-in com fontes reais; nenhuma chamada paga ou retry de LLM."""

import json
import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.adapters.factory import create_adapter
from app.modules.ai.chat.service import ChatService
from app.modules.ai.generation import GenerationService
from app.modules.ai.orchestration.settings import Config
from app.modules.ai.schemas.execution import RunRequest
from app.modules.knowledge.embeddings.encoder import E5Encoder
from app.modules.knowledge.preparation import prepare_corpus
from app.modules.knowledge.retrieval.contracts import Request
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from app.modules.onboarding.schemas import Completion, DraftChange, DraftData
from app.modules.onboarding.service import complete_draft, save_draft
from app.modules.training.publication import published_workout
from app.policies.access import Actor
from scripts.seed_catalog import load_catalog, seed_catalog
from tests.ai.test_triage import BASE
from tests.ai.test_triage_integration import seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions

ROOT = Path(__file__).resolve().parents[3]
QUESTION = "Quanto tempo é recomendavel de exercicio na esteira por dia?"
Scenario = tuple[dict[str, Actor], Retriever, RagEvidence]


@pytest.fixture
def live_corpus(
    sessions: sessionmaker[Session], tmp_path: Path, request: pytest.FixtureRequest
) -> Iterator[Scenario]:
    route = getattr(request.node, "callspec", None)
    if route and os.environ.get("ACADEMIA_TEST_LLM_REAL") != route.params["route"]:
        pytest.skip("Selecionar explicitamente uma rota; consome quota gratuita.")
    if os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1":
        pytest.skip("Ensaio exige E5 local explícito.")
    people = seed(sessions)
    encoder = E5Encoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        prepare_corpus(
            sessions,
            people["admin"].user_id,
            CorpusStorage(tmp_path / "corpus"),
            store,
            encoder,
            root=ROOT,
            artifacts=tmp_path / "ingestao",
        )
        retriever = Retriever(sessions, store, encoder)
        yield people, retriever, RagEvidence(retriever, sessions, store.check)
    finally:
        encoder.close()
        store.close()


@pytest.mark.integration
def test_real_aerobic_coverage_and_out_of_scope(live_corpus: Scenario) -> None:
    people, retriever, _ = live_corpus
    questions = [
        QUESTION,
        "Quantos minutos de caminhada moderada por semana para adultos?",
        "Quanto tempo de corrida vigorosa por semana?",
        "Posso dividir os exercícios em blocos durante o dia?",
    ]
    for question in questions:
        package = retriever.retrieve(
            Request(
                contexto_id=people["cliente"].user_id,
                finalidade="DUVIDAS",
                consulta=question,
            )
        )
        assert package.estado == "EVIDENCIAS_ENCONTRADAS", (question, package.motivo)
        assert any("Guia de Atividade" in e.titulo for e in package.evidencias), (
            question
        )
        if question == QUESTION:
            assert "150" in " ".join(e.texto for e in package.evidencias)
    cases = json.loads((ROOT / "docs/testes/rag05-consultas-v1.json").read_text("utf8"))
    for case in cases["consultas"]:
        package = retriever.retrieve(
            Request(
                contexto_id=people["cliente"].user_id,
                finalidade="DUVIDAS",
                consulta=case["consulta"],
            )
        )
        assert (package.estado != "EVIDENCIAS_ENCONTRADAS") == case["deve_abster"], (
            case["id"]
        )


@pytest.mark.integration
@pytest.mark.parametrize("route", ["generation", "chat"])
def test_live_generation_publication_and_aerobic_chat(
    live_corpus: Scenario, sessions: sessionmaker[Session], route: str
) -> None:
    if os.environ.get("ACADEMIA_TEST_LLM_REAL") != route:
        pytest.skip("Selecionar explicitamente uma rota; consome quota gratuita.")
    people, _, evidence = live_corpus
    client = people["cliente"]
    with sessions.begin() as session:
        seed_catalog(session, people["admin"].user_id, load_catalog())
        draft = save_draft(
            session,
            client.user_id,
            client.user_id,
            DraftChange(
                versao_base=None,
                revisao=None,
                dados=DraftData.model_validate(
                    {
                        **BASE,
                        "dias_semana": 2,
                        "duracao_sessao_min": 80,
                        "objetivo_principal": "HIPERTROFIA",
                        "experiencia": "INICIANTE",
                    }
                ),
            ),
        )
        complete_draft(
            session,
            client.user_id,
            client.user_id,
            Completion(versao_base=None, revisao=draft.revisao),
        )
    adapter = create_adapter(Config.load())
    try:
        generator = GenerationService(sessions, llm=adapter, evidence=evidence)
        request = RunRequest(
            solicitacao_id=uuid4(),
            finalidade="GERACAO" if route == "generation" else "DUVIDA",
            mensagem="" if route == "generation" else QUESTION,
        )
        if route == "generation":
            result = generator.generate(client, client.user_id, request)
            assert result.estado == "PUBLICADA", (result.estado, result.motivo)
            with sessions.begin() as session:
                workout = published_workout(session, client, client.user_id)
                assert workout and len(workout.ficha.dias) == 2
                assert all(1 <= len(day.itens) <= 4 for day in workout.ficha.dias)
                assert workout.parecer.estado == "PENDENTE"
            assert generator.generate(client, client.user_id, request) == result
        else:
            chat = ChatService(sessions, generator)
            result = chat.ask(client, request)
            assert result.estado == "RESPOSTA_PRONTA", (result.estado, result.motivo)
            assert result.resposta and result.resposta.idioma == "pt-BR"
            assert "150" in result.resposta.texto and result.resposta.evidencias_ids
            assert chat.ask(client, request) == result
        report_path = os.environ.get("ACADEMIA_TEST_LIVE_REPORT")
        if report_path:
            Path(report_path).write_text(
                json.dumps(
                    {
                        "rota": route,
                        "estado": result.estado,
                        "motivo": result.motivo,
                        "modelo": result.modelo,
                        "prompts": result.versao_prompts,
                        "configuracao_sha256": result.configuracao_sha256,
                        "consumo": [c.model_dump(mode="json") for c in result.consumo],
                        "resposta": result.resposta.texto if result.resposta else None,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf8",
            )
    finally:
        adapter.close()

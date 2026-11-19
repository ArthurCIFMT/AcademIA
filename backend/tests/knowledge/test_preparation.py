import hashlib
import json
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.main import create_app
from app.modules.identity.models import Role
from app.modules.identity.settings import AuthSettings
from app.modules.knowledge.ingestion.contracts import Page, ParsedDocument, State
from app.modules.knowledge.ingestion.index_models import Ingestion
from app.modules.knowledge.ingestion.indexing import Indexer, available_ingestions
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.models import DocumentVersion
from app.modules.knowledge.preparation import (
    PLAN,
    ReviewedSource,
    load_preparation,
    prepare_corpus,
    verify_selection,
)
from app.modules.knowledge.schemas import Decision
from app.modules.knowledge.service import CorpusError, approved_references, decide
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from tests.knowledge.test_corpus import ORIGIN, PASSWORD, people
from tests.knowledge.test_indexing import FakeEncoder, synthetic
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_plan_rejects_traversal_and_unauthorized_purpose(
    tmp_path: Path,
) -> None:
    selections = load_preparation(ROOT)
    assert len(selections) == 5
    assert {s.source.fonte_id for s in selections} == {
        "BR-RBCM-001",
        "BR-NAHAS-001",
        "INT-HEALTH-001",
    }
    plan = json.loads((ROOT / PLAN).read_text("utf-8"))
    plan["fontes"][0]["selecao"] = "../fora-do-repositorio.json"
    (tmp_path / PLAN).parent.mkdir(parents=True)
    (tmp_path / PLAN).write_text(json.dumps(plan), "utf-8")
    approved = tmp_path / "materiais/rag/corpus-inicial.json"
    approved.write_bytes((ROOT / "materiais/rag/corpus-inicial.json").read_bytes())
    with pytest.raises(ValueError):
        load_preparation(tmp_path)
    plan["fontes"] = [plan["fontes"][0]]
    plan["fontes"][0]["selecao"] = "selecao.json"
    plan["fontes"][0]["finalidades"] = ["TRIAGEM"]
    (tmp_path / "selecao.json").write_bytes(
        (ROOT / "docs/testes/rag05-consultas-v1.json").read_bytes()
    )
    (tmp_path / PLAN).write_text(json.dumps(plan), "utf-8")
    with pytest.raises(ValueError, match="SELECAO_FORA_DA_CURADORIA"):
        load_preparation(tmp_path)


def test_changed_extract_cannot_be_indexed_as_reviewed_content(tmp_path: Path) -> None:
    _, _, extraction, _ = synthetic(tmp_path)
    text = "Trecho de demonstração; preservar unidades e negações."
    source = ReviewedSource(
        fonte_id="SINTETICO",
        arquivo_sha256=extraction.arquivo_sha256,
        trechos=[
            {
                "pagina": 1,
                "inicio": 0,
                "fim": len(text),
                "secao": "Demonstração",
                "texto_hash": hashlib.sha256(text.encode()).hexdigest(),
            }
        ],
    )
    page = Page(
        numero=1,
        texto=text,
        texto_sha256=hashlib.sha256(text.encode()).hexdigest(),
        situacao="TEXTO",
    )
    valid = extraction.model_copy(
        update={
            "resultado": ParsedDocument(estado=State.CONCLUIDA, paginas=[page]),
        }
    )
    verify_selection(valid, source)
    changed = text.replace("preservar", "eliminar")
    altered = page.model_copy(update={"texto": changed})
    invalid = valid.model_copy(
        update={
            "resultado": ParsedDocument.model_construct(
                estado=State.CONCLUIDA, paginas=[altered]
            ),
        }
    )
    with pytest.raises(ValueError, match="RECORTE_DIVERGENTE"):
        verify_selection(invalid, source)


@pytest.mark.integration
def test_prepare_real_sources_replays_and_does_not_revive_revoked_source(
    sessions: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    actor = people(sessions)[Role.ADMINISTRADOR]
    storage = CorpusStorage(tmp_path / "corpus")
    encoder = FakeEncoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        first = prepare_corpus(
            sessions,
            actor.user_id,
            storage,
            store,
            encoder,
            root=ROOT,
            artifacts=tmp_path / "artefatos",
        )
        assert first.importacao.documentos == 19
        assert first.importacao.aprovadas == 9
        assert all(item.indexacao.estado == "CONCLUIDA" for item in first.ingestoes)
        assert len(first.ingestoes) == 5 and store.check().points == 24
        # Simula seleção antiga do mesmo preparo, retirada do manifesto atual.
        book = next(
            item
            for item in load_preparation(ROOT)
            if item.source.fonte_id == "BR-NAHAS-001"
        )
        with sessions.begin() as session:
            ref = next(
                r
                for r in approved_references(session)
                if r.sha256 == book.source.arquivo_sha256
            )
        extraction = Extractor(
            storage,
            policy=book.policy,
            root=tmp_path / "artefatos/extracoes",
        ).extract(ref, approval_check=lambda *_: True)
        obsolete = Indexer(
            sessions,
            store,
            encoder,
            lock_root=tmp_path / "artefatos/indexacao",
        ).run(
            actor,
            extraction,
            book.selection.model_copy(update={"finalidade": "DUVIDAS"}),
        )
        assert store.check().points == 29
        calls = len(encoder.calls)
        second = prepare_corpus(
            sessions,
            actor.user_id,
            storage,
            store,
            encoder,
            root=ROOT,
            artifacts=tmp_path / "artefatos",
        )
        assert second.importacao.versoes_novas == 0
        assert second.ingestoes == first.ingestoes and len(encoder.calls) == calls
        with sessions.begin() as session:
            assert session.scalar(select(func.count()).select_from(Ingestion)) == 6
            retired = session.get(Ingestion, obsolete.id)
            assert retired is not None and retired.estado == "REVOGADA"
            assert obsolete.id not in available_ingestions(
                session, store.check().collection, encoder.space.fingerprint
            )
            # A origem é obtida pela ingestão; IDs de versão e ingestão são distintos.
            ingestion = session.get(Ingestion, first.ingestoes[0].indexacao.id)
            assert ingestion is not None
            version = session.get(DocumentVersion, ingestion.documento_versao_id)
            assert version is not None
            decide(
                session,
                actor,
                version.id,
                Decision(revisao=version.revision, estado="REVOGADO", motivo="Ensaio"),
                storage,
                uuid4(),
            )
        with pytest.raises(ValueError, match="VERSAO_NAO_APROVADA"):
            prepare_corpus(
                sessions,
                actor.user_id,
                storage,
                store,
                encoder,
                root=ROOT,
                artifacts=tmp_path / "artefatos",
            )
        assert store.check().points == 29
    finally:
        store.close()


@pytest.mark.integration
def test_prepare_requires_active_curator(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        with pytest.raises(CorpusError):
            prepare_corpus(
                sessions,
                uuid4(),
                CorpusStorage(tmp_path / "corpus"),
                store,
                FakeEncoder(),
                root=ROOT,
            )
    finally:
        store.close()


@pytest.mark.integration
@pytest.mark.anyio
async def test_default_api_blocks_curators_even_if_the_admin_knows_the_url(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    people(sessions)
    monkeypatch.delenv("ACADEMIA_CORPUS_HTTP_ENABLED", raising=False)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )
    assert "/api/v1/corpus" not in app.openapi()["paths"]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=ORIGIN,
        headers={"Origin": ORIGIN},
    ) as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "administrador@example.test",
                "senha": PASSWORD,
            },
        )
        assert login.status_code == 200
        headers = {"X-CSRF-Token": login.json()["csrf_token"]}
        assert (await client.get("/api/v1/corpus")).status_code == 404
        assert (
            await client.post("/api/v1/corpus/importacao-inicial", headers=headers)
        ).status_code == 404

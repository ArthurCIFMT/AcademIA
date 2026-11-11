import hashlib
import os
import re
from collections.abc import Callable, Iterator, Sequence
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, func, inspect, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.knowledge.embeddings.encoder import (
    E5Encoder,
    EmbeddingError,
    validate_vectors,
)
from app.modules.knowledge.embeddings.settings import REVISION, EmbeddingSettings
from app.modules.knowledge.ingestion.chunking import (
    ChunkingError,
    Selection,
    Span,
    make_chunks,
)
from app.modules.knowledge.ingestion.contracts import ExtractionResult, State
from app.modules.knowledge.ingestion.index_models import Fragment, Ingestion
from app.modules.knowledge.ingestion.indexing import (
    Indexer,
    available_ingestions,
)
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.schemas import Decision, Metadata
from app.modules.knowledge.service import (
    ApprovedReference,
    approved_references,
    decide,
    is_approved,
    register,
)
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.contracts import EmbeddingSpace
from app.modules.knowledge.vector.points import Payload
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from app.modules.people.profiles import EmployeeProfile
from app.policies.access import Actor

ROOT = Path(__file__).resolve().parents[3]


class FakeEncoder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail_on: int | None = None
        self.rate_limits = 0
        self.hard_fail_after: int | None = None
        self.hook: Callable[[], None] = lambda: None

    @property
    def space(self) -> EmbeddingSpace:
        return EmbeddingSpace(
            model="intfloat/multilingual-e5-small", revision=REVISION, dimension=384
        )

    def tokens(self, text: str) -> int:
        return len(re.findall(r"\w+|[^\w\s]", text)) + 2

    def passages(self, texts: Sequence[str], timeout: float) -> list[list[float]]:
        self.calls.append(list(texts))
        self.hook()
        if self.hard_fail_after is not None and len(self.calls) > self.hard_fail_after:
            raise EmbeddingError("SERVICO_INDISPONIVEL")
        if self.rate_limits:
            self.rate_limits -= 1
            raise EmbeddingError("RATE_LIMIT", transient=True)
        if self.fail_on == len(self.calls):
            raise EmbeddingError("TIMEOUT", transient=True)
        return [[1.0] + [0.0] * 383 for _ in texts]


def synthetic(
    tmp_path: Path, *, text: str | None = None
) -> tuple[CorpusStorage, ApprovedReference, ExtractionResult, Selection]:
    storage = CorpusStorage(tmp_path / "originais")
    body = text or "\n\n".join(
        f"Parágrafo {n}. Não exceder 10 kg; limite >= 20 s e <= 40 s. "
        + "exemplo sintético " * 75
        for n in range(3)
    )
    ref, sha = storage.store(body.encode(), "TXT")
    metadata = Metadata(
        titulo="Documento sintético",
        origem_url="https://example.test/fixture",
        licenca="Fixture",
        idioma="pt-BR",
        finalidades=["DUVIDAS"],
        limites="Não usar como evidência real.",
    )
    reference = ApprovedReference(uuid4(), 2, sha, ref, "TXT", metadata)
    extraction = Extractor(storage, root=tmp_path / "extracao", parser=parse).extract(
        reference, approval_check=lambda *_: True
    )
    spans, offset = [], 0
    for paragraph in body.split("\n\n"):
        spans.append(
            Span(
                pagina=None,
                inicio=offset,
                fim=offset + len(paragraph),
                secao="Seção sintética",
            )
        )
        offset += len(paragraph) + 2
    selection = Selection(
        finalidade="DUVIDAS",
        motivo_curadoria="Amostra sintética do teste",
        trechos=spans,
    )
    return storage, reference, extraction, selection


def test_chunks_preserve_atoms_symbols_overlap_and_provenance(tmp_path: Path) -> None:
    _, _, extraction, selection = synthetic(tmp_path)
    encoder = FakeEncoder()
    id = uuid4()
    chunks = make_chunks(extraction, selection, encoder, id)
    assert len(chunks) >= 2
    assert make_chunks(extraction, selection, encoder, id) == chunks
    for chunk in chunks:
        assert chunk.tokens <= 300 and chunk.input_tokens <= 512
        assert (
            "Não exceder 10 kg" in chunk.texto
            and ">= 20 s" in chunk.texto
            and "<= 40 s" in chunk.texto
        )
        assert chunk.pagina is None and chunk.linha_inicio is not None
        assert hashlib.sha256(chunk.texto.encode()).hexdigest() == chunk.texto_hash
    assert not encoder.calls


@pytest.mark.parametrize("kind", ["PARAGRAFO", "TABELA"])
def test_large_atomic_content_requires_treatment_without_truncation(
    tmp_path: Path, kind: str
) -> None:
    _, _, extraction, selection = synthetic(tmp_path, text="não perder ressalva " * 400)
    selection = selection.model_copy(
        update={"trechos": [selection.trechos[0].model_copy(update={"tipo": kind})]}
    )
    with pytest.raises(ChunkingError, match="EXCEDE_LIMITE"):
        make_chunks(extraction, selection, FakeEncoder(), uuid4())


def test_nonconcluded_or_unapproved_purpose_and_cut_word_are_refused(
    tmp_path: Path,
) -> None:
    _, _, extraction, selection = synthetic(
        tmp_path, text="Não exceder 10 kg.\n\nPreservar esta restrição."
    )
    with pytest.raises(ChunkingError, match="FINALIDADE_NAO_APROVADA"):
        make_chunks(
            extraction,
            selection.model_copy(update={"finalidade": "TRIAGEM"}),
            FakeEncoder(),
            uuid4(),
        )
    bad = extraction.model_copy(
        update={
            "resultado": extraction.resultado.model_copy(
                update={"estado": State.REVISAO_NECESSARIA}
            )
        }
    )
    with pytest.raises(ChunkingError, match="EXTRACAO_NAO_CONCLUIDA"):
        make_chunks(bad, selection, FakeEncoder(), uuid4())
    with pytest.raises(ChunkingError, match="CORTA_PALAVRA"):
        make_chunks(
            extraction,
            selection.model_copy(
                update={"trechos": [Span(pagina=None, inicio=1, fim=4)]}
            ),
            FakeEncoder(),
            uuid4(),
        )


@pytest.mark.parametrize(
    "vectors",
    [[], [[0.0] * 384], [[1.0] * 384], [[float("nan")] + [0.0] * 383], [[1.0] * 3]],
)
def test_invalid_embeddings_are_rejected(vectors: list[list[float]]) -> None:
    with pytest.raises(EmbeddingError):
        validate_vectors(vectors, 1, 384)


def test_retry_is_bounded_and_only_for_transient_embedding_errors(
    tmp_path: Path,
) -> None:
    from unittest.mock import MagicMock

    encoder = FakeEncoder()
    encoder.rate_limits = 3
    indexer = Indexer(MagicMock(), MagicMock(), encoder, sleep=lambda _: None)
    _, _, extraction, selection = synthetic(tmp_path, text="Não exceder 10 kg.")
    chunks = make_chunks(extraction, selection, encoder, uuid4())
    with pytest.raises(EmbeddingError, match="RATE_LIMIT"):
        indexer._vectors(chunks)
    assert len(encoder.calls) == 3
    encoder.rate_limits, encoder.calls = 2, []
    assert len(indexer._vectors(chunks)) == 1
    assert len(encoder.calls) == 3


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(str(ROOT / "database/alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                yield connection, config
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def sessions(migration: tuple[Connection, Config]) -> sessionmaker[Session]:
    connection, config = migration
    command.upgrade(config, "head")
    return create_session_factory(connection)


def setup(
    sessions: sessionmaker[Session], tmp_path: Path, *, text: str | None = None
) -> tuple[Actor, CorpusStorage, ApprovedReference, ExtractionResult, Selection]:
    storage, reference, extraction, selection = synthetic(tmp_path, text=text)
    with sessions.begin() as session:
        user = create_account(
            session,
            "curador-indexacao@example.test",
            state=AccountState.ATIVO,
            password_hash=Passwords().hash("senha-sintetica-indexacao"),
            now=utc_now(),
        )
        session.add(UserRole(id=uuid4(), usuario_id=user, papel=Role.ADMINISTRADOR))
        session.add(
            EmployeeProfile(
                usuario_id=user,
                nome="Curador sintético",
                cargo="Administrador",
                ativo=True,
                data_admissao=date(2026, 1, 1),
            )
        )
        session.flush()
        actor = Actor(user, frozenset({Role.ADMINISTRADOR}))
        row, _ = register(
            session,
            actor,
            "INDEX-001",
            "LITERATURA",
            reference.metadata,
            "TXT",
            len(storage.read(reference.reference, reference.sha256)),
            reference.reference,
            reference.sha256,
            uuid4(),
        )
        decide(
            session,
            actor,
            row.id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )
        ref = approved_references(session)[0]

    def approved(id: UUID, revision: int) -> bool:
        with sessions.begin() as session:
            return is_approved(session, id, revision)

    extraction = Extractor(
        storage, root=tmp_path / "real-extraction", parser=parse
    ).extract(ref, approval_check=approved)
    return actor, storage, ref, extraction, selection


@pytest.mark.integration
def test_partial_failure_resumes_only_missing_points_and_replay_is_idempotent(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, _, _, extraction, selection = setup(sessions, tmp_path)
    encoder = FakeEncoder()
    encoder.hard_fail_after = 1
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        indexer = Indexer(
            sessions,
            store,
            encoder,
            lock_root=tmp_path / "locks",
            batch_size=1,
            sleep=lambda _: None,
        )
        first = indexer.run(actor, extraction, selection)
        assert first.estado == "FALHA" and first.indexados == 1 and first.total > 1
        with sessions.begin() as session:
            assert (
                available_ingestions(
                    session, store.settings.collection, encoder.space.fingerprint
                )
                == []
            )
        encoder.hard_fail_after = None
        before = len(encoder.calls)
        complete = indexer.run(actor, extraction, selection)
        assert complete.estado == "CONCLUIDA" and complete.indexados == complete.total
        assert len(encoder.calls) - before == complete.total - 1
        calls = len(encoder.calls)
        assert indexer.run(actor, extraction, selection) == complete
        assert len(encoder.calls) == calls and store.check().points == complete.total
        with sessions.begin() as session:
            assert available_ingestions(
                session, store.settings.collection, encoder.space.fingerprint
            ) == [complete.id]
            assert (
                session.scalar(select(func.count()).select_from(Fragment))
                == complete.total
            )
    finally:
        store.close()


@pytest.mark.integration
def test_revocation_during_embedding_prevents_activation(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, storage, ref, extraction, selection = setup(sessions, tmp_path)
    encoder = FakeEncoder()

    def revoke() -> None:
        with sessions.begin() as session:
            decide(
                session,
                actor,
                ref.version_id,
                Decision(revisao=2, estado="REVOGADO", motivo="Teste"),
                storage,
                uuid4(),
            )

    encoder.hook = revoke
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        result = Indexer(
            sessions, store, encoder, lock_root=tmp_path / "locks", sleep=lambda _: None
        ).run(actor, extraction, selection)
        assert result.estado == "REVOGADA" and store.check().points == 0
        with sessions.begin() as session:
            assert (
                available_ingestions(
                    session, store.settings.collection, encoder.space.fingerprint
                )
                == []
            )
    finally:
        store.close()


@pytest.mark.integration
def test_large_table_is_recorded_pending_without_vectors(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, _, _, extraction, selection = setup(sessions, tmp_path)
    selection = selection.model_copy(
        update={
            "trechos": [
                Span(
                    pagina=None,
                    inicio=0,
                    fim=len(extraction.resultado.paginas[0].texto),
                    tipo="TABELA",
                )
            ]
        }
    )
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        result = Indexer(
            sessions, store, FakeEncoder(), lock_root=tmp_path / "locks"
        ).run(actor, extraction, selection)
        assert (
            result.estado == "PENDENTE_TRATAMENTO"
            and result.erro_codigo == "TABELA_EXCEDE_LIMITE"
        )
        assert store.check().points == 0
    finally:
        store.close()


@pytest.mark.database
def test_migration_roundtrip_constraints_and_immutable_provenance(
    migration: tuple[Connection, Config], tmp_path: Path
) -> None:
    connection, config = migration
    command.upgrade(config, "0012")
    assert not inspect(connection).has_table("ingestao", schema="academia")
    command.upgrade(config, "head")
    command.check(config)
    factory = create_session_factory(connection)
    actor, _, _, extraction, selection = setup(factory, tmp_path)
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        result = Indexer(
            factory, store, FakeEncoder(), lock_root=tmp_path / "locks"
        ).run(actor, extraction, selection)
        with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
            session.execute(
                update(Ingestion)
                .where(Ingestion.id == result.id)
                .values(plano_hash="0" * 64)
            )
        with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
            session.execute(update(Fragment).values(texto_hash="0" * 64))
    finally:
        store.close()
    command.downgrade(config, "0012")
    assert not inspect(connection).has_table("fragmento", schema="academia")


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1",
    reason="Ensaio real E5 opt-in; exige pesos locais provisionados.",
)
def test_real_e5_cpu_tokenizer_vectors_and_query_prefix() -> None:
    encoder = E5Encoder(EmbeddingSettings())
    try:
        assert encoder.tokens("passage: Não exceder 10 kg.") < 512
        vectors = encoder.passages(["Atividade física e exercícios de força."], 90)
        queries = encoder.queries(["O que é exercício de força?"], 30)
        validate_vectors(vectors, 1, 384)
        validate_vectors(queries, 1, 384)
        assert encoder.space.revision == REVISION
    finally:
        encoder.close()


def test_worker_timeout_kills_process_and_does_not_return_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    encoder = E5Encoder()
    process = MagicMock()
    process.poll.return_value = None
    encoder._process = process
    monkeypatch.setattr(encoder, "tokens", lambda _: 4)
    with pytest.raises(EmbeddingError, match="TIMEOUT"):
        encoder.passages(["Texto sintético"], 0.01)
    process.kill.assert_called_once()
    assert encoder._process is None


@pytest.mark.parametrize(
    "code,transient,calls", [("TIMEOUT", True, 3), ("SAIDA_INVALIDA", False, 1)]
)
def test_retry_differentiates_timeout_from_invalid_output(
    tmp_path: Path,
    code: str,
    transient: bool,
    calls: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    encoder = FakeEncoder()
    provider = MagicMock(side_effect=EmbeddingError(code, transient=transient))
    monkeypatch.setattr(encoder, "passages", provider)
    _, _, extraction, selection = synthetic(
        tmp_path, text="Texto sintético, sem dados pessoais."
    )
    chunks = make_chunks(extraction, selection, encoder, uuid4())
    indexer = Indexer(MagicMock(), MagicMock(), encoder, sleep=lambda _: None)
    with pytest.raises(EmbeddingError, match=code):
        indexer._vectors(chunks)
    assert provider.call_count == calls


@pytest.mark.integration
def test_checkpoint_crash_window_reuses_persisted_vectors_without_new_embedding(
    sessions: sessionmaker[Session], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor, _, _, extraction, selection = setup(sessions, tmp_path)
    encoder = FakeEncoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    original = store.present
    checks = 0

    def interrupt(expected: dict[UUID, Payload]) -> set[UUID]:
        nonlocal checks
        checks += 1
        if checks == 2:
            from app.modules.knowledge.vector.contracts import (
                VectorError,
                VectorErrorCode,
            )

            raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL)
        return original(expected)

    monkeypatch.setattr(store, "present", interrupt)
    try:
        indexer = Indexer(
            sessions, store, encoder, lock_root=tmp_path / "locks", batch_size=1
        )
        failed = indexer.run(actor, extraction, selection)
        assert (
            failed.estado == "FALHA"
            and failed.indexados == 0
            and store.check().points == 1
        )
        calls = len(encoder.calls)
        complete = indexer.run(actor, extraction, selection)
        assert complete.estado == "CONCLUIDA"
        assert len(encoder.calls) - calls == complete.total - 1
    finally:
        store.close()


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1",
    reason="Exige pesos E5 reais provisionados.",
)
def test_real_e5_postgres_qdrant_pipeline(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, _, _, extraction, selection = setup(sessions, tmp_path)
    text = extraction.resultado.paginas[0].texto
    end = text.index(". Não exceder") + 1
    selection = Selection(
        finalidade="DUVIDAS",
        motivo_curadoria="Amostra técnica sintética de integração real",
        trechos=[Span(pagina=None, inicio=0, fim=end)],
    )
    encoder = E5Encoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        indexer = Indexer(sessions, store, encoder, lock_root=tmp_path / "locks")
        result = indexer.run(actor, extraction, selection)
        assert result.estado == "CONCLUIDA" and result.total == result.indexados == 1
        assert indexer.run(actor, extraction, selection) == result
        assert store.check().points == 1
        with sessions.begin() as session:
            assert available_ingestions(
                session, store.settings.collection, encoder.space.fingerprint
            ) == [result.id]
    finally:
        encoder.close()
        store.close()


@pytest.mark.integration
def test_replay_repairs_corrupted_payload_without_duplicating_points(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, _, _, extraction, selection = setup(sessions, tmp_path)
    encoder = FakeEncoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        indexer = Indexer(sessions, store, encoder, lock_root=tmp_path / "locks")
        complete = indexer.run(actor, extraction, selection)
        with sessions.begin() as session:
            fragment = session.scalar(
                select(Fragment).where(Fragment.ingestao_id == complete.id)
            )
            assert fragment is not None
            point_id = fragment.id
        assert store._client is not None
        store._client.set_payload(
            store.settings.collection,
            payload={"texto": "Conteúdo corrompido; não usar como evidência."},
            points=[str(point_id)],
        )
        previous = len(encoder.calls)
        recovered = indexer.run(actor, extraction, selection)
        assert recovered.estado == "CONCLUIDA"
        assert len(encoder.calls) == previous + 1
        assert store.check().points == recovered.total == complete.total
        assert indexer.run(actor, extraction, selection) == recovered
    finally:
        store.close()

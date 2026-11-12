import asyncio
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError
from qdrant_client import QdrantClient, models

from app.main import create_app
from app.modules.knowledge.vector.__main__ import main
from app.modules.knowledge.vector.contracts import (
    VectorError,
    VectorErrorCode,
    VectorStore,
)
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.runtime import close_vector_store, get_vector_store
from app.modules.knowledge.vector.settings import VectorSettings

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    close_vector_store()
    for name in os.environ:
        if name.startswith("ACADEMIA_VECTOR_"):
            monkeypatch.delenv(name)
    yield
    close_vector_store()


def policy(path: Path) -> VectorSettings:
    return VectorSettings(path=str(path))


def fake_client(settings: VectorSettings) -> MagicMock:
    space = settings.space
    client = MagicMock(spec=QdrantClient)
    client.collection_exists.return_value = True
    client.get_collection.return_value = SimpleNamespace(
        config=SimpleNamespace(
            params=SimpleNamespace(
                vectors=models.VectorParams(
                    size=space.dimension, distance=models.Distance.COSINE
                ),
                sparse_vectors=None,
            ),
            metadata={
                "academia": {
                    "schema_version": 1,
                    "embedding_space": space.model_dump(mode="json"),
                    "space_sha256": space.fingerprint,
                }
            },
        ),
        points_count=0,
    )
    return client


def test_default_space_matches_approved_configuration(tmp_path: Path) -> None:
    settings = policy(tmp_path)
    canonical = json.loads(
        (ROOT / "docs/requisitos/schemas/configuracao-ia-v2.json").read_text()
    )
    space = settings.space
    assert space.model == canonical["embedding"]["model"]
    assert space.dimension == canonical["embedding"]["dimension"] == 384
    assert space.metric.lower() == canonical["retrieval"]["metric"]
    assert space.normalized == canonical["embedding"]["normalize"]
    assert space.query_prefix == canonical["embedding"]["query_prefix"]
    assert space.passage_prefix == canonical["embedding"]["passage_prefix"]
    assert space.revision == "614241f622f53c4eeff9890bdc4f31cfecc418b3"  # RAG-04
    assert (
        settings.model_copy(
            update={"embedding_model": "outro-modelo"}
        ).space.fingerprint
        != space.fingerprint
    )
    assert (
        settings.model_copy(update={"model_revision": "a" * 40}).space.fingerprint
        != space.fingerprint
    )


@pytest.mark.parametrize(
    "values",
    [
        {"mode": "remote"},
        {"path": ":memory:"},
        {"path": " "},
        {"url": "https://segredo.example.test"},
        {"collection": "../externa"},
        {"collection": "sem_versao"},
        {"dimension": 0},
        {"embedding_model": " "},
        {"model_revision": "nao-e-um-hash"},
    ],
)
def test_configuration_rejects_ephemeral_or_unsupported_modes(
    values: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        VectorSettings.model_validate(values)


def test_lazy_adapter_serializes_threads_and_releases_connection(
    tmp_path: Path,
) -> None:
    settings = policy(tmp_path)
    client = fake_client(settings)
    factory = MagicMock(return_value=client)
    store: VectorStore = QdrantStore(settings, client_factory=factory)
    factory.assert_not_called()
    with ThreadPoolExecutor(max_workers=8) as pool:
        reports = list(pool.map(lambda _: store.check(), range(8)))
    factory.assert_called_once_with(tmp_path.resolve())
    client.create_collection.assert_not_called()
    assert all(report == reports[0] for report in reports)
    store.close()
    store.close()
    client.close.assert_called_once()


@pytest.mark.parametrize(
    "mismatch",
    [
        "dimension",
        "metric",
        "model",
        "revision",
        "hash",
        "named",
        "sparse",
        "missing_metadata",
    ],
)
def test_existing_incompatible_collection_is_never_adopted_or_recreated(
    tmp_path: Path, mismatch: str
) -> None:
    settings = policy(tmp_path)
    client = fake_client(settings)
    info = client.get_collection.return_value
    if mismatch == "dimension":
        info.config.params.vectors.size = 768
    elif mismatch == "metric":
        info.config.params.vectors.distance = models.Distance.DOT
    elif mismatch == "model":
        info.config.metadata["academia"]["embedding_space"]["model"] = "outro-modelo"
    elif mismatch == "revision":
        info.config.metadata["academia"]["embedding_space"]["revision"] = "b" * 40
    elif mismatch == "hash":
        info.config.metadata["academia"]["space_sha256"] = "0" * 64
    elif mismatch == "named":
        info.config.params.vectors = {"outro": info.config.params.vectors}
    elif mismatch == "sparse":
        info.config.params.sparse_vectors = {"sparse": {}}
    else:
        info.config.metadata = None
    with pytest.raises(VectorError) as error:
        QdrantStore(settings, client_factory=MagicMock(return_value=client)).check()
    assert error.value.code == VectorErrorCode.CONFIGURACAO_INCOMPATIVEL
    client.create_collection.assert_not_called()
    client.recreate_collection.assert_not_called()
    client.delete_collection.assert_not_called()
    client.close.assert_called_once()


def test_unavailability_is_controlled_without_stale_success_or_retry(
    tmp_path: Path,
) -> None:
    settings = policy(tmp_path)
    client = fake_client(settings)
    factory = MagicMock(return_value=client)
    store = QdrantStore(settings, client_factory=factory)
    store.check()
    client.get_collection.side_effect = OSError("caminho privado com segredo")
    with pytest.raises(VectorError) as error:
        store.check()
    assert error.value.code == VectorErrorCode.SERVICO_INDISPONIVEL
    assert "segredo" not in str(error.value)
    factory.assert_called_once()
    client.close.assert_called_once()
    # Outra ação explícita tenta reconectar; nenhuma tentativa oculta na falha.
    factory.side_effect = RuntimeError("lock ocupado")
    with pytest.raises(VectorError):
        store.check()
    assert factory.call_count == 2
    client.recreate_collection.assert_not_called()


def test_singleton_is_lazy_and_shared_by_threads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import app.modules.knowledge.vector.runtime as runtime

    monkeypatch.setenv("ACADEMIA_VECTOR_PATH", str(tmp_path))
    factory = MagicMock(return_value=MagicMock(spec=VectorStore))
    monkeypatch.setattr(runtime, "QdrantStore", factory)
    with ThreadPoolExecutor(max_workers=8) as pool:
        stores = list(pool.map(lambda _: get_vector_store(), range(16)))
    assert len({id(store) for store in stores}) == 1
    factory.assert_called_once()
    factory.return_value.check.assert_not_called()
    close_vector_store()
    factory.return_value.close.assert_called_once()


def test_adapter_does_not_reuse_client_after_process_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    factory = MagicMock()
    store = QdrantStore(policy(tmp_path), client_factory=factory)
    monkeypatch.setattr("app.modules.knowledge.vector.qdrant.os.getpid", lambda: -1)
    with pytest.raises(VectorError) as error:
        store.check()
    assert error.value.code == VectorErrorCode.SERVICO_INDISPONIVEL
    factory.assert_not_called()


def test_cli_invalid_configuration_has_private_json_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ACADEMIA_VECTOR_URL", "https://usuario:segredo@example.test")
    assert main() == 1
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["code"] == "CONFIGURACAO_INVALIDA"
    assert "segredo" not in captured.out + captured.err
    assert not captured.err


def test_api_remains_available_without_opening_vector_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.knowledge.vector.qdrant as adapter

    factory = MagicMock(side_effect=RuntimeError("indisponível"))
    monkeypatch.setattr(adapter, "_new_client", factory)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    monkeypatch.setenv("ACADEMIA_VECTOR_MODE", "remote")

    async def verify() -> None:
        app = create_app()
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as api:
                assert (await api.get("/health")).json() == {"status": "ok"}
                assert not any(
                    "vector" in route
                    for route in (await api.get("/openapi.json")).json()["paths"]
                )

    asyncio.run(verify())
    factory.assert_not_called()


@pytest.mark.integration
def test_real_qdrant_persists_metadata_and_synthetic_vector_after_reconnect(
    tmp_path: Path,
) -> None:
    settings = policy(tmp_path / "qdrant")
    store = QdrantStore(settings)
    initial = store.check()
    assert (initial.dimension, initial.metric, initial.points) == (384, "Cosine", 0)
    store.close()
    vector = [1.0] + [0.0] * 383
    point_id = str(uuid4())
    with closing(QdrantClient(path=str(settings.directory))) as native:
        native.upsert(
            settings.collection,
            [
                models.PointStruct(
                    id=point_id, vector=vector, payload={"fixture": "sintetica"}
                )
            ],
        )
    reopened = QdrantStore(settings)
    try:
        report = reopened.check()
        assert report.points == 1
        assert report.space_sha256 == initial.space_sha256
    finally:
        reopened.close()
    with closing(QdrantClient(path=str(settings.directory))) as native:
        result = native.query_points(settings.collection, query=vector, limit=1)
        assert result.points[0].id == point_id
        assert result.points[0].score == pytest.approx(1.0)
        assert result.points[0].payload == {"fixture": "sintetica"}


@pytest.mark.integration
@pytest.mark.parametrize(
    "mismatch", ["dimension", "metric", "model", "missing_metadata"]
)
def test_real_incompatible_collection_preserves_existing_data(
    tmp_path: Path, mismatch: str
) -> None:
    settings = policy(tmp_path / "qdrant")
    size = 12 if mismatch == "dimension" else 384
    metadata: dict[str, object] | None = {
        "academia": {
            "schema_version": 1,
            "embedding_space": settings.space.model_dump(mode="json"),
            "space_sha256": settings.space.fingerprint,
        }
    }
    if mismatch == "model":
        metadata = {"academia": {"embedding_space": {"model": "outro"}}}
    if mismatch == "missing_metadata":
        metadata = None
    with closing(QdrantClient(path=str(settings.directory))) as native:
        native.create_collection(
            settings.collection,
            vectors_config=models.VectorParams(
                size=size,
                distance=models.Distance.DOT
                if mismatch == "metric"
                else models.Distance.COSINE,
            ),
            metadata=metadata,
        )
        native.upsert(
            settings.collection,
            [models.PointStruct(id=str(uuid4()), vector=[1.0] + [0.0] * (size - 1))],
        )
    store = QdrantStore(settings)
    with pytest.raises(VectorError) as error:
        store.check()
    assert error.value.code == VectorErrorCode.CONFIGURACAO_INCOMPATIVEL
    store.close()
    with closing(QdrantClient(path=str(settings.directory))) as native:
        assert native.get_collection(settings.collection).points_count == 1
        assert native.get_collection(settings.collection).config.metadata == metadata


def cli_env(settings: VectorSettings) -> dict[str, str]:
    return {
        **os.environ,
        "ACADEMIA_VECTOR_PATH": str(settings.directory),
        "ACADEMIA_VECTOR_COLLECTION": settings.collection,
        "PYTHONPATH": str(ROOT / "backend"),
    }


@pytest.mark.integration
def test_other_process_cannot_share_directory_and_cli_recovers_after_release(
    tmp_path: Path,
) -> None:
    settings = policy(tmp_path / "qdrant")
    store = QdrantStore(settings)
    store.check()
    try:
        blocked = subprocess.run(
            [sys.executable, "-m", "app.modules.knowledge.vector"],
            env=cli_env(settings),
            cwd=ROOT / "backend",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        assert blocked.returncode == 1
        assert json.loads(blocked.stdout)["code"] == "SERVICO_INDISPONIVEL"
        assert str(settings.directory) not in blocked.stdout + blocked.stderr
    finally:
        store.close()
    for _ in range(2):
        success = subprocess.run(
            [sys.executable, "-m", "app.modules.knowledge.vector"],
            env=cli_env(settings),
            cwd=ROOT / "backend",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        assert success.returncode == 0, success.stderr
        assert json.loads(success.stdout) == {"status": "OK", **asdict(store.check())}
        store.close()


@pytest.mark.integration
def test_storage_failure_is_controlled_and_does_not_create_memory_fallback(
    tmp_path: Path,
) -> None:
    target = tmp_path / "arquivo"
    target.write_text("Não é um diretório de banco.")
    store = QdrantStore(policy(target))
    with pytest.raises(VectorError) as error:
        store.check()
    assert error.value.code == VectorErrorCode.SERVICO_INDISPONIVEL
    assert target.read_text() == "Não é um diretório de banco."
    store.close()


@pytest.mark.integration
def test_fastapi_shutdown_releases_singleton_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = policy(tmp_path / "qdrant")
    monkeypatch.setenv("ACADEMIA_VECTOR_PATH", str(settings.directory))
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")

    async def verify() -> None:
        app = create_app()
        async with app.router.lifespan_context(app):
            with ThreadPoolExecutor(max_workers=4) as pool:
                reports = list(pool.map(lambda _: get_vector_store().check(), range(8)))
            assert len({report.space_sha256 for report in reports}) == 1
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as api:
                assert (await api.get("/health")).status_code == 200

    asyncio.run(verify())
    # Se o shutdown não liberasse o singleton, outro cliente seria recusado pelo lock.
    with closing(QdrantClient(path=str(settings.directory))) as independent:
        assert independent.get_collection(settings.collection).points_count == 0

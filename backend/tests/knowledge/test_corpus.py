import json
import shutil
from base64 import b64encode
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, delete, func, inspect, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.audit.models import AuditRecord
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.knowledge.catalog import import_initial
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.knowledge.schemas import Decision, Metadata, VersionView
from app.modules.knowledge.service import (
    CorpusError,
    approved_references,
    decide,
    is_approved,
    register,
)
from app.modules.knowledge.storage import CorpusStorage, InvalidFile, decode_file
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor

ROOT = Path(__file__).resolve().parents[3]
ORIGIN = "https://academia.example.test"
PASSWORD = "senha-sintetica-rag01"
URL = "/api/v1/corpus"
PDF = b"%PDF-1.4\nDocumento sintetico para teste de armazenamento.\n%%EOF"
META = {
    "titulo": "Documento sintético",
    "origem_url": "https://example.test/fonte",
    "licenca": "Fixture de teste",
    "idioma": "pt-BR",
    "finalidades": ["DUVIDAS"],
    "limites": "Documento artificial; não é evidência científica.",
    "paginas_declaradas": 1,
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            tx = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(str(ROOT / "database" / "alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                yield connection, config
            finally:
                tx.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def sessions(migration: tuple[Connection, Config]) -> sessionmaker[Session]:
    connection, config = migration
    command.upgrade(config, "head")
    return create_session_factory(connection)


def people(sessions: sessionmaker[Session]) -> dict[Role, Actor]:
    password = Passwords().hash(PASSWORD)
    result = {}
    with sessions.begin() as session:
        for role in Role:
            user = create_account(
                session,
                role.value.lower() + "@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=user, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=user,
                        nome="Cliente sintético",
                        ativo=True,
                        data_nascimento=date(1990, 1, 1),
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=user,
                        nome=role.value,
                        cargo=role.value,
                        ativo=True,
                        data_admissao=date(2026, 1, 1),
                    )
                )
            result[role] = Actor(user, frozenset({role}))
    return result


def add(
    session: Session,
    actor: Actor,
    storage: CorpusStorage,
    content: bytes = PDF,
    scope: str = "LITERATURA",
    catalog: str = "TESTE-001",
) -> tuple[VersionView, bool]:
    reference, digest = storage.store(content, "PDF")
    return register(
        session,
        actor,
        catalog,
        scope,
        Metadata.model_validate(META),
        "PDF",
        len(content),
        reference,
        digest,
        uuid4(),
    )


@pytest.mark.parametrize(
    "encoded,format",
    [
        ("!inválido!", "PDF"),
        (b64encode(b"texto").decode(), "PDF"),
        (b64encode(b"\xff").decode(), "TXT"),
        (b64encode(b"a\x00b").decode(), "TXT"),
        (b64encode(b"   ").decode(), "TXT"),
    ],
)
def test_invalid_files(encoded: str, format: str) -> None:
    with pytest.raises(InvalidFile):
        decode_file(encoded, format)


def test_storage_is_integral_and_does_not_accept_paths(tmp_path: Path) -> None:
    storage = CorpusStorage(tmp_path)
    ref, digest = storage.store(PDF, "PDF")
    assert storage.read(ref, digest) == PDF
    assert storage.store(PDF, "PDF") == (ref, digest)
    with pytest.raises(InvalidFile):
        storage.read("../externo.pdf", digest)
    storage.path(ref).write_bytes(b"corrompido")
    with pytest.raises(InvalidFile):
        storage.store(PDF, "PDF")


def test_schema_and_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    api = create_app().openapi()
    assert URL + "/{version_id}/decisao" in api["paths"]
    schema = api["components"]["schemas"]["RegisterDocument"]
    assert schema["additionalProperties"] is False
    assert "arquivo_base64" in schema["required"]
    with pytest.raises(ValueError):
        Decision(revisao=1, estado="REVOGADO", motivo=" ")


@pytest.mark.integration
@pytest.mark.anyio
async def test_private_api_versioning_decisions_and_cache_revocation(
    sessions: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actors = people(sessions)
    monkeypatch.setenv("ACADEMIA_CORPUS_DIR", str(tmp_path))
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=ORIGIN,
        headers={"Origin": ORIGIN},
    ) as client:
        assert (await client.get(URL)).status_code == 401
        for role in (Role.CLIENTE, Role.ATENDENTE, Role.INSTRUTOR):
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": role.value.lower() + "@example.test", "senha": PASSWORD},
            )
            assert login.status_code == 200
            assert (await client.get(URL)).status_code == 403
            assert (await client.get(URL + f"/{uuid4()}/arquivo")).status_code == 403
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "administrador@example.test", "senha": PASSWORD},
        )
        headers = {"X-CSRF-Token": login.json()["csrf_token"]}
        payload = {
            "catalogo_id": "TESTE-001",
            "ambiente": "LITERATURA",
            "formato": "PDF",
            "metadados": META,
            "arquivo_base64": b64encode(PDF).decode(),
            "conteudo_literatura_confirmado": True,
        }
        assert (await client.post(URL, json=payload)).status_code == 403
        created = await client.post(URL, json=payload, headers=headers)
        assert created.status_code == 201
        first = created.json()
        assert first["estado"] == "PENDENTE" and "arquivo_ref" not in first
        assert (await client.post(URL, json=payload, headers=headers)).json()[
            "id"
        ] == first["id"]
        next_version = (
            await client.post(
                URL,
                json={
                    **payload,
                    "arquivo_base64": b64encode(PDF + b"\nsegunda").decode(),
                },
                headers=headers,
            )
        ).json()
        assert (
            next_version["numero"] == 2
            and next_version["documento_id"] == first["documento_id"]
        )
        with sessions.begin() as session:
            assert approved_references(session) == []
        approve = {"revisao": 1, "estado": "APROVADO", "motivo": None}
        approved = await client.post(
            URL + "/" + first["id"] + "/decisao", json=approve, headers=headers
        )
        assert approved.status_code == 200
        assert approved.json()["aprovado_por"] == str(
            actors[Role.ADMINISTRADOR].user_id
        )
        assert (
            await client.post(
                URL + "/" + first["id"] + "/decisao", json=approve, headers=headers
            )
        ).json() == approved.json()
        with sessions.begin() as session:
            reference = approved_references(session)[0]
            assert is_approved(session, reference.version_id, reference.revision)
        exported = await client.get(URL + "/" + first["id"] + "/arquivo")
        assert (
            exported.content == PDF and exported.headers["cache-control"] == "no-store"
        )
        revoke = {
            "revisao": 2,
            "estado": "REVOGADO",
            "motivo": "Revisão técnica sintética",
        }
        assert (
            await client.post(
                URL + "/" + first["id"] + "/decisao", json=revoke, headers=headers
            )
        ).status_code == 200
        with sessions.begin() as session:
            assert not is_approved(session, reference.version_id, reference.revision)
            assert approved_references(session) == []
            assert (
                session.scalar(select(func.count()).select_from(DocumentVersion)) == 2
            )
        assert (await client.post(URL, json=payload, headers=headers)).json()[
            "estado"
        ] == "REVOGADO"
        assert (await client.get(URL)).json()["total"] == 2
        assert (await client.get(URL + "/" + first["id"])).json()[
            "aprovado_por"
        ] is not None
        assert (
            await client.post(
                URL + "/" + first["id"] + "/decisao", json=approve, headers=headers
            )
        ).status_code == 409
        test_version = (
            await client.post(
                URL, json={**payload, "ambiente": "TESTE"}, headers=headers
            )
        ).json()
        await client.post(
            URL + "/" + test_version["id"] + "/decisao", json=approve, headers=headers
        )
        with sessions.begin() as session:
            assert approved_references(session) == []
        assert (await client.get(URL + "?ambiente=TESTE")).json()["total"] == 1


@pytest.mark.integration
def test_real_initial_catalog_import_is_idempotent_and_keeps_revocation(
    sessions: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    admin = people(sessions)[Role.ADMINISTRADOR]
    storage = CorpusStorage(tmp_path)
    with sessions.begin() as session:
        first = import_initial(
            session, admin, storage, uuid4(), ROOT / "materiais" / "rag"
        )
        assert (
            first.documentos,
            first.versoes_novas,
            first.aprovadas,
            first.pendentes,
        ) == (18, 18, 7, 11)
        again = import_initial(
            session, admin, storage, uuid4(), ROOT / "materiais" / "rag"
        )
        assert again.versoes_novas == 0
        approved = approved_references(session)
        assert len(approved) == 7
        current = approved[0]
        decide(
            session,
            admin,
            current.version_id,
            Decision(revisao=current.revision, estado="REVOGADO", motivo="Teste"),
            storage,
            uuid4(),
        )
        assert (
            import_initial(
                session, admin, storage, uuid4(), ROOT / "materiais" / "rag"
            ).revogadas
            == 1
        )
        assert len(approved_references(session)) == 6
        assert session.scalar(select(func.count()).select_from(Document)) == 18


@pytest.mark.database
def test_migration_preserves_immutable_provenance(
    migration: tuple[Connection, Config], tmp_path: Path
) -> None:
    connection, config = migration
    command.upgrade(config, "0011")
    assert not inspect(connection).has_table("documento", schema="academia")
    command.upgrade(config, "head")
    command.check(config)
    factory = create_session_factory(connection)
    admin = people(factory)[Role.ADMINISTRADOR]
    storage = CorpusStorage(tmp_path)
    with factory.begin() as session:
        row, _ = add(session, admin, storage)
    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(
            update(DocumentVersion)
            .where(DocumentVersion.id == row.id)
            .values(metadados={"titulo": "troca"})
        )
    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(delete(Document))
    with factory.begin() as session:
        storage.path(row.sha256 + ".pdf").write_bytes(b"corrompido")
        with pytest.raises(CorpusError) as error:
            decide(
                session,
                admin,
                row.id,
                Decision(revisao=1, estado="APROVADO"),
                storage,
                uuid4(),
            )
        assert error.value.status == 409
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditRecord)
                .where(AuditRecord.acao == "corpus.approved")
            )
            == 0
        )
    command.downgrade(config, "0011")
    assert not inspect(connection).has_table("documento", schema="academia")


@pytest.mark.integration
@pytest.mark.parametrize("same_content", [True, False])
def test_concurrent_versions(same_content: bool, tmp_path: Path) -> None:
    engine = create_database_engine("test")
    schema = "rag01_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            admin = people(factory)[Role.ADMINISTRADOR]
            storage = CorpusStorage(tmp_path)
            barrier = Barrier(2)

            def run(index: int) -> UUID:
                barrier.wait(timeout=10)
                with factory.begin() as session:
                    row, _ = add(
                        session,
                        admin,
                        storage,
                        PDF if same_content else PDF + str(index).encode(),
                    )
                    return row.id

            with ThreadPoolExecutor(max_workers=2) as pool:
                ids = list(pool.map(run, [0, 1]))
            assert len(set(ids)) == (1 if same_content else 2)
            with factory.begin() as session:
                assert list(
                    session.scalars(
                        select(DocumentVersion.numero).order_by(DocumentVersion.numero)
                    )
                ) == ([1] if same_content else [1, 2])
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()


def test_metadata_preserves_complete_authorship_and_rejects_nul() -> None:
    authors = [f"Autor sintético {i}" for i in range(24)]
    assert Metadata.model_validate({**META, "autores": authors}).autores == authors
    with pytest.raises(ValueError):
        Metadata.model_validate({**META, "autores": ["inválido\x00"]})


@pytest.mark.integration
def test_catalog_hash_failure_does_not_register_partial_corpus(
    sessions: sessionmaker[Session],
    tmp_path: Path,
) -> None:
    admin = people(sessions)[Role.ADMINISTRADOR]
    materials = tmp_path / "materiais"
    shutil.copytree(ROOT / "materiais" / "rag", materials)
    catalog = json.loads((materials / "catalogo.json").read_text(encoding="utf-8-sig"))
    last = materials / catalog["documentos"][-1]["arquivo"]
    last.write_bytes(b"arquivo modificado")
    with sessions.begin() as session:
        with pytest.raises(CorpusError) as error:
            import_initial(
                session, admin, CorpusStorage(tmp_path / "blobs"), uuid4(), materials
            )
        assert error.value.status == 409
        assert session.scalar(select(func.count()).select_from(Document)) == 0
        assert session.scalar(select(func.count()).select_from(DocumentVersion)) == 0

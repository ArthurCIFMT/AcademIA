from base64 import b64encode
from collections.abc import Iterator
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from PIL import Image, PngImagePlugin
from sqlalchemy import Connection, inspect, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.equipment.http import MAX_WRITE_BYTES
from app.modules.equipment.images import (
    InvalidEquipmentImage,
    LocalEquipmentImages,
    normalize_image,
)
from app.modules.equipment.models import Equipment
from app.modules.equipment.service import (
    EquipmentUnavailable,
    available_resources,
    read_resources,
    require_available,
)
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import EmployeeProfile

_ADMIN = "/api/v1/admin/equipamentos"
_CATALOG = "/api/v1/equipamentos"
_ORIGIN = "https://academia.example.test"
_PASSWORD = "senha-sintetica-eqp01"
_ROOT = Path(__file__).resolve().parents[3]


def photo(*, size: tuple[int, int] = (32, 24), format: str = "PNG") -> str:
    with Image.new("RGB", size, "steelblue") as image:
        data = BytesIO()
        info = PngImagePlugin.PngInfo()
        info.add_text("Comment", "metadado sintético")
        image.save(data, format=format, pnginfo=info)
    return b64encode(data.getvalue()).decode("ascii")


def test_image_is_decoded_resized_and_stored_without_metadata(tmp_path: Path) -> None:
    storage = LocalEquipmentImages(tmp_path)
    output = normalize_image(photo(size=(1400, 700)))
    reference = storage.store(output)
    assert reference == storage.store(output)
    assert list(tmp_path.iterdir()) == [tmp_path / f"{reference}.png"]
    assert storage.read(reference) == output
    assert storage.read("../arquivo") is None
    with Image.open(BytesIO(output)) as image:
        assert image.format == "PNG" and image.size == (1200, 600)
        assert image.info == {}
    with Image.open(BytesIO(normalize_image(photo(format="JPEG")))) as image:
        assert image.format == "PNG"


@pytest.mark.parametrize(
    "encoded",
    [
        "!invalido!",
        b64encode(b"arquivo de texto").decode(),
        photo(format="GIF"),
        photo(size=(2049, 1)),
    ],
)
def test_image_rejects_unsupported_content_and_dimensions(encoded: str) -> None:
    with pytest.raises(InvalidEquipmentImage):
        normalize_image(encoded)


def test_equipment_routes_document_json_and_png(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    openapi = create_app().openapi()
    paths = openapi["paths"]
    assert "get" in paths[_CATALOG]
    assert "application/json" in paths[_ADMIN]["post"]["requestBody"]["content"]
    assert "413" in paths[_ADMIN]["post"]["responses"]
    image = paths[_CATALOG + "/{equipment_id}/imagem"]["get"]["responses"]["200"]
    assert "image/png" in image["content"]
    schemas = openapi["components"]["schemas"]
    assert {"nome", "ativo", "operacional", "solicitacao_id"} <= set(
        schemas["EquipmentCreate"]["required"]
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(str(_ROOT / "database" / "alembic.ini"))
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


def seed_staff(sessions: sessionmaker[Session]) -> None:
    password = Passwords().hash(_PASSWORD)
    with sessions.begin() as session:
        for role, name in (
            (Role.ADMINISTRADOR, "admin"),
            (Role.ATENDENTE, "atendente"),
        ):
            actor = create_account(
                session,
                f"{name}@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=actor, papel=role))
            session.add(
                EmployeeProfile(
                    usuario_id=actor,
                    nome=name,
                    cargo=role,
                    data_admissao=date(2026, 1, 1),
                    ativo=True,
                )
            )


async def login(browser: httpx.AsyncClient, name: str) -> dict[str, str]:
    result = await browser.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.test", "senha": _PASSWORD},
    )
    assert result.status_code == 200
    return {"X-CSRF-Token": result.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
async def test_admin_inventory_public_catalog_and_resource_revalidation(
    sessions: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    monkeypatch.setenv("ACADEMIA_EQUIPMENT_IMAGES_DIR", str(tmp_path))
    seed_staff(sessions)
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    api = httpx.ASGITransport(app=app)
    body = {
        "solicitacao_id": str(uuid4()),
        "nome": "  Remo sintético  ",
        "categoria": "Cardio",
        "descricao": "Equipamento da demonstração",
        "ativo": True,
        "operacional": True,
        "imagem_base64": photo(),
    }

    def browser() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=api, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        )

    async with browser() as visitor, browser() as admin, browser() as attendant:
        assert (await visitor.get(_CATALOG)).json()["itens"] == []
        assert (await visitor.get(_ADMIN)).status_code == 401
        staff_headers = await login(attendant, "atendente")
        assert (await attendant.get(_ADMIN)).status_code == 403
        assert (
            await attendant.post(_ADMIN, json=body, headers=staff_headers)
        ).status_code == 403
        headers = await login(admin, "admin")
        assert (await admin.post(_ADMIN, json=body)).status_code == 403
        too_large = await admin.post(
            _ADMIN,
            content=b" " * (MAX_WRITE_BYTES + 1),
            headers={**headers, "Content-Type": "application/json"},
        )
        assert too_large.status_code == 413
        for invalid in (
            {**body, "nome": " "},
            {key: value for key, value in body.items() if key != "operacional"},
            {**body, "ativo": "true"},
            {**body, "imagem_base64": "invalid"},
        ):
            assert (
                await admin.post(_ADMIN, json=invalid, headers=headers)
            ).status_code == 422
        assert not list(tmp_path.iterdir())

        result = await admin.post(_ADMIN, json=body, headers=headers)
        assert result.status_code == 201
        item = result.json()
        equipment_id = UUID(item["id"])
        path = _ADMIN + "/" + str(equipment_id)
        assert item["nome"] == "Remo sintético" and item["revisao"] == 1
        assert (await admin.get(path)).json() == item
        assert (await admin.post(_ADMIN, json=body, headers=headers)).json() == item
        assert (
            await admin.post(_ADMIN, json={**body, "nome": "Outro"}, headers=headers)
        ).status_code == 409
        assert (await admin.get(_ADMIN)).json()["total"] == 1
        offered = (await visitor.get(_CATALOG)).json()["itens"]
        assert len(offered) == 1
        assert set(offered[0]) == {"id", "nome", "categoria", "descricao", "imagem_url"}
        assert offered[0]["categoria"] == "Cardio"
        public_image = offered[0]["imagem_url"]
        image = await visitor.get(public_image)
        assert image.status_code == 200 and image.headers["content-type"] == "image/png"
        assert image.headers["x-content-type-options"] == "nosniff"
        assert image.headers["cache-control"] == "no-store"
        with sessions.begin() as session:
            assert [row.id for row in available_resources(session)] == [equipment_id]
            require_available(session, [equipment_id])
            assert read_resources(session, [equipment_id])[equipment_id].disponivel

        metadata = {
            key: value
            for key, value in body.items()
            if key not in {"solicitacao_id", "imagem_base64"}
        }
        unavailable = await admin.put(
            path, json={**metadata, "revisao": 1, "operacional": False}, headers=headers
        )
        assert unavailable.status_code == 200 and unavailable.json()["revisao"] == 2
        assert (
            await admin.put(path, json={**metadata, "revisao": 1}, headers=headers)
        ).status_code == 409
        assert (await visitor.get(_CATALOG)).json()["itens"] == []
        assert (await visitor.get(public_image)).status_code == 404
        assert (await admin.get(unavailable.json()["imagem_url"])).status_code == 200
        missing = uuid4()
        with sessions.begin() as session:
            with pytest.raises(EquipmentUnavailable) as error:
                require_available(session, [equipment_id, missing])
            assert error.value.ids == {equipment_id, missing}

        inactive = await admin.put(
            path,
            json={**metadata, "revisao": 2, "ativo": False, "imagem_base64": None},
            headers=headers,
        )
        assert inactive.status_code == 200 and inactive.json()["imagem_url"] is None
        assert inactive.json()["id"] == item["id"]
        assert (await admin.get(_ADMIN)).json()["total"] == 1
        assert (await visitor.get(_CATALOG)).json()["total"] == 0
        with sessions.begin() as session:
            assert read_resources(session, [equipment_id])[equipment_id].ativo is False
            with pytest.raises(EquipmentUnavailable):
                require_available(session, [equipment_id])


@pytest.mark.database
def test_equipment_migration_and_fresh_locking_read(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0007")
    assert not inspect(connection).has_table("equipamento", schema="academia")
    command.upgrade(config, "0008")
    command.check(config)
    factory = create_session_factory(connection)
    equipment_id = uuid4()
    with factory.begin() as session:
        session.add(
            Equipment(
                id=equipment_id,
                nome="Supino sintético",
                ativo=True,
                operacional=True,
                revision=1,
            )
        )
    with (
        pytest.raises(IntegrityError, match="ck_equipamento_nome"),
        factory.begin() as session,
    ):
        session.add(
            Equipment(id=uuid4(), nome=" ", ativo=True, operacional=True, revision=1)
        )
    with factory.begin() as session:
        cached = session.get(Equipment, equipment_id)
        assert cached is not None and cached.operacional
        session.execute(
            update(Equipment)
            .where(Equipment.id == equipment_id)
            .values(operacional=False)
            .execution_options(synchronize_session=False)
        )
        assert cached.operacional
        with pytest.raises(EquipmentUnavailable):
            require_available(session, [equipment_id])
    command.downgrade(config, "0007")
    assert not inspect(connection).has_table("equipamento", schema="academia")

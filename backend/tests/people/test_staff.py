import re
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from email.message import EmailMessage
from os import environ
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
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
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.identity.models import AccessToken, AccountState, Role, User, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.roles import active_admin_ids
from app.modules.identity.service import digest, utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.email import EmailDelivery
from app.modules.notifications.models import DeliveryState, Notification
from app.modules.people import invitations, staff
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor

_ORIGIN = "https://academia.example.test"
_URL = "/api/v1/funcionarios"
_ADMIN = "admin@example.test"
_PASSWORD = "senha-sintetica-pes01"
_DATE = date(2026, 1, 1)


@pytest.fixture
def sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                ini = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
                config = Config(str(ini))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield create_session_factory(connection)
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def passwords() -> Passwords:
    return Passwords()


@pytest.fixture
def admin(sessions: sessionmaker[Session], passwords: Passwords) -> UUID:
    with sessions.begin() as session:
        return bootstrap_admin(
            session,
            email=_ADMIN,
            name="Admin inicial",
            hired_on=_DATE,
            password=_PASSWORD,
            passwords=passwords,
            now=utc_now(),
        )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def api(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as browser:
        yield browser


async def _sign_in(api: httpx.AsyncClient, email: str) -> str:
    response = await api.post(
        "/api/v1/auth/login", json={"email": email, "senha": _PASSWORD}
    )
    assert response.status_code == 200
    token: str = response.json()["csrf_token"]
    return token


def _form(email: str) -> dict[str, object]:
    return {
        "email": email,
        "nome": "Pessoa Sintética",
        "cargo": "Instrutor",
        "data_admissao": _DATE.isoformat(),
        "papeis": ["INSTRUTOR"],
    }


def _update(stored: dict[str, object], **changes: object) -> dict[str, object]:
    fields = ("nome", "cargo", "data_admissao", "papeis", "ativo", "revisao")
    return {**{key: stored[key] for key in fields}, **changes}


def _mailpit_token(email: str) -> str:
    with httpx.Client(
        base_url="http://127.0.0.1:8025", trust_env=False, timeout=5
    ) as sink:
        search = sink.get("/api/v1/search", params={"query": f"to:{email}"})
        search.raise_for_status()
        messages = search.json()["messages"]
        assert len(messages) == 1
        message = sink.get(f"/api/v1/message/{messages[0]['ID']}")
        message.raise_for_status()
    token = re.search(
        rf"{re.escape(_ORIGIN)}/primeiro-acesso#token=([A-Za-z0-9_-]{{43}})",
        message.json()["Text"],
    )
    assert token is not None
    return token.group(1)


def test_staff_routes_have_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "201" in paths[_URL]["post"]["responses"]
    assert "200" in paths[_URL + "/{user_id}"]["put"]["responses"]
    assert "429" in paths[_URL + "/{user_id}/convite"]["post"]["responses"]


def test_staff_input_rejects_client_role_and_trims_names() -> None:
    data = staff.CreateStaff.model_validate(
        {**_form("x@example.test"), "nome": " Pessoa "}
    )
    assert data.nome == "Pessoa"
    with pytest.raises(ValueError):
        staff.CreateStaff.model_validate(
            {**_form("x@example.test"), "papeis": ["CLIENTE"]}
        )


@pytest.mark.integration
@pytest.mark.anyio
async def test_staff_creation_mailpit_first_access_and_direct_api_authorization(
    sessions: sessionmaker[Session], admin: UUID, api: httpx.AsyncClient
) -> None:
    if environ.get("ACADEMIA_TEST_MAILPIT") != "1":
        pytest.skip("Inicie o Mailpit e habilite ACADEMIA_TEST_MAILPIT=1.")
    email = f"pes01-{uuid4()}@example.test"
    assert (await api.get(_URL)).status_code == 401
    csrf = await _sign_in(api, _ADMIN)
    assert (await api.post(_URL, json=_form(email))).status_code == 403
    headers = {"X-CSRF-Token": csrf}

    created = await api.post(_URL, json=_form(email), headers=headers)
    assert created.status_code == 201
    staff_id = UUID(created.json()["id"])
    data = created.json()
    assert data["estado_conta"] == "CONVIDADO"
    assert data["convite"]["estado"] == "ENVIADO"
    assert (await api.get(f"{_URL}/{staff_id}")).json() == data
    assert (await api.get(_URL, params={"limite": 1, "pagina": 2})).json()["itens"][0][
        "id"
    ] == str(staff_id)
    assert (
        await api.post(_URL, json=_form(email.upper()), headers=headers)
    ).status_code == 409
    invalid = {**_form("invalid@example.test"), "papeis": ["CLIENTE"]}
    assert (await api.post(_URL, json=invalid, headers=headers)).status_code == 422

    token = _mailpit_token(email)
    with sessions.begin() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 2
        assert session.scalar(select(func.count()).select_from(EmployeeProfile)) == 2
        access = session.scalar(
            select(AccessToken).where(AccessToken.usuario_id == staff_id)
        )
        assert access is not None and access.hash == digest(token)
        audit = session.scalar(
            select(AuditRecord).where(AuditRecord.recurso_id == staff_id)
        )
        assert (
            audit is not None
            and audit.ator_id == admin
            and audit.acao == "staff.created"
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.destinatario_id == admin,
                    Notification.tipo == "ALTERACAO_CRITICA",
                )
            )
            == 1
        )

    api.cookies.clear()
    credentials = {"token": token, "senha": _PASSWORD}
    assert (
        await api.post("/api/v1/auth/first-access", json=credentials)
    ).status_code == 204
    assert (
        await api.post("/api/v1/auth/first-access", json=credentials)
    ).status_code == 401
    employee_csrf = await _sign_in(api, email)
    assert (await api.get("/api/v1/auth/session")).json()["roles"] == ["INSTRUTOR"]
    assert (await api.get(_URL)).status_code == 403
    assert (
        await api.put(
            f"{_URL}/{staff_id}",
            json=_update(data),
            headers={"X-CSRF-Token": employee_csrf},
        )
    ).status_code == 403


@pytest.mark.integration
@pytest.mark.anyio
async def test_existing_client_retains_its_role_and_updates_are_revision_checked(
    sessions: sessionmaker[Session],
    admin: UUID,
    api: httpx.AsyncClient,
    passwords: Passwords,
) -> None:
    email = "cliente@example.test"
    with sessions.begin() as session:
        existing = create_account(
            session,
            email,
            state=AccountState.ATIVO,
            password_hash=passwords.hash(_PASSWORD),
            now=utc_now(),
        )
        session.add_all(
            [
                ClientProfile(
                    usuario_id=existing,
                    nome="Cliente",
                    data_nascimento=_DATE,
                    ativo=True,
                ),
                UserRole(id=uuid4(), usuario_id=existing, papel=Role.CLIENTE),
            ]
        )

    headers = {"X-CSRF-Token": await _sign_in(api, _ADMIN)}
    assert (await api.post(_URL, json=_form(email), headers=headers)).status_code == 409
    linked = await api.post(
        _URL, json={**_form(email), "vincular_existente": True}, headers=headers
    )
    assert linked.status_code == 201 and linked.json()["id"] == str(existing)
    assert linked.json()["convite"] is None
    initial = linked.json()
    update = _update(initial, nome="Nome atualizado", ativo=False)
    result = await api.put(f"{_URL}/{existing}", json=update, headers=headers)
    assert result.status_code == 200
    assert result.json()["ativo"] is False
    assert (await api.get(f"{_URL}/{existing}")).json()["nome"] == "Nome atualizado"
    assert (
        await api.put(f"{_URL}/{existing}", json=update, headers=headers)
    ).status_code == 409

    current_admin = (await api.get(f"{_URL}/{admin}")).json()
    for denied in (
        _update(current_admin, ativo=False),
        _update(current_admin, papeis=["ATENDENTE"]),
    ):
        assert (
            await api.put(f"{_URL}/{admin}", json=denied, headers=headers)
        ).status_code == 409

    api.cookies.clear()
    await _sign_in(api, email)
    assert (await api.get("/api/v1/auth/session")).json()["roles"] == ["CLIENTE"]
    with sessions.begin() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 2
        history = set(
            session.scalars(
                select(AuditRecord.acao).where(AuditRecord.recurso_id == existing)
            )
        )
        assert history == {"staff.created", "staff.deactivated"}


class CaptureMail:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.state = DeliveryState.FALHOU

    def deliver(self, message: EmailMessage) -> DeliveryState:
        self.messages.append(str(message.get_content()))
        return self.state


@pytest.mark.integration
@pytest.mark.anyio
async def test_failed_invite_can_be_reissued_and_old_link_is_revoked(
    admin: UUID, api: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert admin
    sender = CaptureMail()
    monkeypatch.setattr(
        invitations,
        "local_email_delivery",
        lambda factory: EmailDelivery(factory, sender, "academia@example.test"),
    )
    headers = {"X-CSRF-Token": await _sign_in(api, _ADMIN)}
    created = await api.post(_URL, json=_form("retry@example.test"), headers=headers)
    assert created.status_code == 201
    assert created.json()["convite"]["estado"] == "FALHOU"
    url = f"{_URL}/{created.json()['id']}/convite"
    revision = {"revisao": created.json()["revisao"]}
    sender.state = DeliveryState.ENVIADO
    fresh = await api.post(url, json=revision, headers=headers)
    assert fresh.status_code == 200 and fresh.json()["convite"]["estado"] == "ENVIADO"
    assert (await api.post(url, json=revision, headers=headers)).status_code == 409
    assert len(sender.messages) == 2
    old = re.search(r"#token=([A-Za-z0-9_-]{43})", sender.messages[0])
    assert old is not None
    assert (
        await api.post(
            "/api/v1/auth/first-access",
            json={"token": old.group(1), "senha": _PASSWORD},
        )
    ).status_code == 401
    third = await api.post(
        url, json={"revisao": fresh.json()["revisao"]}, headers=headers
    )
    assert third.status_code == 200
    assert (
        await api.post(url, json={"revisao": third.json()["revisao"]}, headers=headers)
    ).status_code == 429


@pytest.mark.integration
def test_concurrent_deactivations_preserve_an_active_administrator(
    passwords: Passwords,
) -> None:
    engine = create_database_engine("test")
    schema = "pes01_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            with factory.begin() as session:
                admins = []
                for email in ("primeiro@example.test", "segundo@example.test"):
                    user_id = create_account(
                        session,
                        email,
                        state=AccountState.ATIVO,
                        password_hash=passwords.hash(_PASSWORD),
                        now=utc_now(),
                    )
                    session.add_all(
                        [
                            EmployeeProfile(
                                usuario_id=user_id,
                                nome=email,
                                cargo="Admin",
                                data_admissao=_DATE,
                                ativo=True,
                            ),
                            UserRole(
                                id=uuid4(), usuario_id=user_id, papel=Role.ADMINISTRADOR
                            ),
                        ]
                    )
                    admins.append(user_id)
            barrier = Barrier(2)

            def deactivate(user_id: UUID) -> int:
                barrier.wait(timeout=5)
                try:
                    with factory.begin() as session:
                        staff.update_staff(
                            session,
                            user_id,
                            staff.UpdateStaff(
                                nome="Admin",
                                cargo="Admin",
                                data_admissao=_DATE,
                                papeis={Role.ADMINISTRADOR},
                                ativo=False,
                                revisao=1,
                            ),
                            Actor(user_id, frozenset({Role.ADMINISTRADOR})),
                            uuid4(),
                        )
                except staff.StaffError as exc:
                    return exc.status
                return 200

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(deactivate, admins)) == [200, 409]
            with factory.begin() as session:
                assert len(active_admin_ids(session)) == 1
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

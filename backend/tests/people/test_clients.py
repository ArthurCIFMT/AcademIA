import re
from collections.abc import AsyncIterator, Iterator
from datetime import date
from email.message import EmailMessage
from os import environ
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

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
from app.modules.identity.service import digest, utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.email import EmailDelivery
from app.modules.notifications.models import DeliveryState
from app.modules.people import invitations
from app.modules.people.clients import CreateClient
from app.modules.people.profiles import ClientProfile, EmployeeProfile

_ORIGIN = "https://academia.example.test"
_CLIENTS = "/api/v1/clientes"
_ADMIN = "admin@example.test"
_ATTENDANT = "atendente@example.test"
_PASSWORD = "senha-sintetica-pes02"
_BIRTH = "1990-01-01"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(
                    str(
                        Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
                    )
                )
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield create_session_factory(connection)
            finally:
                outer.rollback()
    finally:
        engine.dispose()


@pytest.fixture
async def api(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    passwords = Passwords()
    today = date(2026, 1, 1)
    now = utc_now()
    with sessions.begin() as db:
        bootstrap_admin(
            db,
            email=_ADMIN,
            name="Admin sintético",
            hired_on=today,
            password=_PASSWORD,
            passwords=passwords,
            now=now,
        )
        user_id = create_account(
            db,
            _ATTENDANT,
            state=AccountState.ATIVO,
            password_hash=passwords.hash(_PASSWORD),
            now=now,
        )
        db.add_all(
            [
                EmployeeProfile(
                    usuario_id=user_id,
                    nome="Atendente sintético",
                    cargo="Atendente",
                    data_admissao=today,
                    ativo=True,
                ),
                UserRole(id=uuid4(), usuario_id=user_id, papel=Role.ATENDENTE),
            ]
        )
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as client:
        yield client


async def _login(api: httpx.AsyncClient, email: str) -> dict[str, str]:
    response = await api.post(
        "/api/v1/auth/login", json={"email": email, "senha": _PASSWORD}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def _form(email: str) -> dict[str, object]:
    return {"email": email, "nome": "Pessoa Sintética", "data_nascimento": _BIRTH}


async def _read_mail(email: str) -> str:
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8025", timeout=5, trust_env=False
    ) as sink:
        response = await sink.get("/api/v1/search", params={"query": f"to:{email}"})
        response.raise_for_status()
        messages = response.json()["messages"]
        assert len(messages) == 1
        message = await sink.get(f"/api/v1/message/{messages[0]['ID']}")
        message.raise_for_status()
    token = re.search(
        rf"{re.escape(_ORIGIN)}/primeiro-acesso#token=([A-Za-z0-9_-]{{43}})",
        message.json()["Text"],
    )
    assert token is not None
    return token.group(1)


def test_validation_and_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "201" in paths[_CLIENTS]["post"]["responses"]
    assert "429" in paths[_CLIENTS + "/{user_id}/convite"]["post"]["responses"]
    data = CreateClient.model_validate({**_form("a@example.test"), "telefone": " "})
    assert data.telefone is None
    with pytest.raises(ValueError):
        CreateClient.model_validate(
            {**_form("a@example.test"), "data_nascimento": "2099-01-01"}
        )


@pytest.mark.integration
@pytest.mark.anyio
async def test_attendant_registration_search_and_first_login(
    api: httpx.AsyncClient, sessions: sessionmaker[Session]
) -> None:
    if environ.get("ACADEMIA_TEST_MAILPIT") != "1":
        pytest.skip("Inicie o Mailpit e habilite ACADEMIA_TEST_MAILPIT=1.")
    email = f"pes02-{uuid4()}@example.test"
    assert (await api.get(_CLIENTS)).status_code == 401
    headers = await _login(api, _ATTENDANT)
    assert (await api.post(_CLIENTS, json=_form(email))).status_code == 403
    created = await api.post(_CLIENTS, json=_form(email.upper()), headers=headers)
    assert created.status_code == 201
    detail = created.json()
    assert detail["email"] == email and detail["estado_conta"] == "CONVIDADO"
    assert detail["convite"]["estado"] == "ENVIADO"
    user_id = UUID(detail["id"])
    url = f"{_CLIENTS}/{user_id}"
    assert (await api.get(url)).json() == detail

    for search in ("  SINTÉTICA  ", email.upper()):
        response = await api.get(_CLIENTS, params={"busca": search, "limite": 1})
        assert response.status_code == 200 and response.json()["total"] == 1
        assert response.json()["itens"][0]["id"] == str(user_id)
    literal = await api.get(_CLIENTS, params={"busca": "%"})
    assert literal.json()["itens"] == []
    assert (
        await api.post(_CLIENTS, json=_form(email), headers=headers)
    ).status_code == 409

    token = await _read_mail(email)
    with sessions.begin() as db:
        row = db.scalar(select(AccessToken).where(AccessToken.usuario_id == user_id))
        assert row is not None and row.hash == digest(token)
        assert db.scalar(select(func.count()).select_from(ClientProfile)) == 1
    api.cookies.clear()
    activation = {"token": token, "senha": _PASSWORD}
    assert (
        await api.post("/api/v1/auth/first-access", json=activation)
    ).status_code == 204
    assert (
        await api.post("/api/v1/auth/first-access", json=activation)
    ).status_code == 401
    await _login(api, email)
    assert (await api.get("/api/v1/auth/session")).json()["roles"] == ["CLIENTE"]
    assert (await api.get(_CLIENTS)).status_code == 403
    assert (await api.get(url)).status_code == 403
    assert (await api.get(f"{_CLIENTS}/{uuid4()}")).status_code == 403


@pytest.mark.integration
@pytest.mark.anyio
async def test_inactivation_preserves_employee_role_and_history(
    api: httpx.AsyncClient, sessions: sessionmaker[Session]
) -> None:
    headers = await _login(api, _ADMIN)
    inactive = "inativo@example.test"
    with sessions.begin() as db:
        create_account(
            db, inactive, state=AccountState.INATIVO, password_hash="", now=utc_now()
        )
    assert (
        await api.post(_CLIENTS, json=_form(inactive), headers=headers)
    ).status_code == 409
    invalid = {**_form("invalido@example.test"), "nome": " "}
    assert (await api.post(_CLIENTS, json=invalid, headers=headers)).status_code == 422
    conflict = await api.post(_CLIENTS, json=_form(_ATTENDANT), headers=headers)
    assert conflict.status_code == 409
    linked = await api.post(
        _CLIENTS,
        json={**_form(_ATTENDANT), "vincular_existente": True},
        headers=headers,
    )
    assert linked.status_code == 201 and linked.json()["convite"] is None
    row = linked.json()
    url = f"{_CLIENTS}/{row['id']}"
    api.cookies.clear()
    headers = await _login(api, _ATTENDANT)
    assert (await api.get("/api/v1/auth/session")).json()["roles"] == [
        "ATENDENTE",
        "CLIENTE",
    ]
    data = {
        "nome": "Nome atualizado",
        "data_nascimento": _BIRTH,
        "telefone": "555-0100",
        "ativo": False,
        "revisao": row["revisao"],
    }
    denied = await api.put(
        url, json={**data, "email": "outro@example.test"}, headers=headers
    )
    assert denied.status_code == 422
    saved = await api.put(url, json=data, headers=headers)
    assert saved.status_code == 200 and saved.json()["ativo"] is False
    assert (await api.get(url)).json()["telefone"] == "555-0100"
    assert (await api.put(url, json=data, headers=headers)).status_code == 409
    assert (await api.get("/api/v1/auth/session")).json()["roles"] == ["ATENDENTE"]

    user_id = UUID(row["id"])
    with sessions.begin() as db:
        account = db.get(User, user_id)
        assert account is not None and account.email == _ATTENDANT
        assert db.scalar(select(func.count()).select_from(User)) == 3
        history = db.scalars(
            select(AuditRecord.acao).where(AuditRecord.recurso_id == user_id)
        )
        assert set(history) == {"client.created", "client.deactivated"}


class CaptureMail:
    def __init__(self) -> None:
        self.state = DeliveryState.FALHOU
        self.bodies: list[str] = []

    def deliver(self, message: EmailMessage) -> DeliveryState:
        self.bodies.append(str(message.get_content()))
        return self.state


@pytest.mark.integration
@pytest.mark.anyio
async def test_failed_invite_can_be_reissued_with_new_token(
    api: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sink = CaptureMail()
    monkeypatch.setattr(
        invitations,
        "local_email_delivery",
        lambda factory: EmailDelivery(factory, sink, "academia@example.test"),
    )
    headers = await _login(api, _ADMIN)
    created = await api.post(
        _CLIENTS, json=_form("retry@example.test"), headers=headers
    )
    assert (
        created.status_code == 201 and created.json()["convite"]["estado"] == "FALHOU"
    )
    row = created.json()
    url = f"{_CLIENTS}/{row['id']}/convite"
    sink.state = DeliveryState.ENVIADO
    data = {"revisao": row["revisao"]}
    sent = await api.post(url, json=data, headers=headers)
    assert sent.status_code == 200 and sent.json()["convite"]["estado"] == "ENVIADO"
    assert (await api.post(url, json=data, headers=headers)).status_code == 409
    assert len(sink.bodies) == 2
    for body, expected in zip(sink.bodies, (401, 204), strict=True):
        match = re.search(r"#token=([A-Za-z0-9_-]{43})", body)
        assert match is not None
        confirmed = await api.post(
            "/api/v1/auth/first-access",
            json={"token": match.group(1), "senha": _PASSWORD},
        )
        assert confirmed.status_code == expected

import json
import re
from asyncio import to_thread
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from os import environ
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, delete, inspect, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.identity.accounts import create_account
from app.modules.identity.first_access import issue_first_access
from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import digest, utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.models import DeliveryState, EmailKind, Notification
from app.modules.onboarding.assessment import CreateAssessment, read_assessment_context
from app.modules.onboarding.invitations import exchange_invitation, issue_invitation
from app.modules.onboarding.invitations_http import RESTRICTED_COOKIE, RESTRICTED_PATH
from app.modules.onboarding.models import (
    Evaluation,
    OnboardingInvitation,
    OnboardingVersion,
)
from app.modules.onboarding.schemas import (
    Completion,
    ConfirmUpdate,
    DraftChange,
    DraftData,
    OnboardingData,
    SnapshotView,
)
from app.modules.onboarding.service import (
    OnboardingError,
    age_at,
    append_evaluation,
    complete_draft,
    confirm_update,
    get_snapshot,
    is_current_snapshot,
    save_draft,
)
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor

_ROOT = Path(__file__).resolve().parents[3]
_FORM: dict[str, object] = json.loads(
    (_ROOT / "docs/testes/contratos-onboarding-v1.json").read_text("utf-8")
)["casos"][0]["entrada"]
_ORIGIN = "https://academia.example.test"
_API = "/api/v1/onboarding/meu"
_INVITES = "/api/v1/onboarding/clientes/{}/convite"
_TRADE = RESTRICTED_PATH + "/troca"
_DRAFT = RESTRICTED_PATH + "/rascunho"
_COMPLETE = RESTRICTED_PATH + "/conclusao"
_PASSWORD = "senha-sintetica-onb02"
_BIRTH = date(1995, 1, 1)


@dataclass(frozen=True)
class People:
    client: UUID
    other: UUID
    instructor: UUID
    attendant: UUID
    replacement: UUID
    admin: UUID


def _seed(factory: sessionmaker[Session], suffix: str = "") -> People:
    password = Passwords().hash(_PASSWORD)
    with factory.begin() as session:

        def add(name: str, role: Role) -> UUID:
            user_id = create_account(
                session,
                f"{name}{suffix}@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=user_id,
                        nome=name,
                        data_nascimento=_BIRTH,
                        ativo=True,
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=user_id,
                        nome=name,
                        cargo=role,
                        data_admissao=date(2026, 1, 1),
                        ativo=True,
                    )
                )
            return user_id

        return People(
            add("cliente", Role.CLIENTE),
            add("outro", Role.CLIENTE),
            add("instrutor", Role.INSTRUTOR),
            add("atendente", Role.ATENDENTE),
            add("substituto", Role.INSTRUTOR),
            add("admin", Role.ADMINISTRADOR),
        )


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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_age_changes_on_birthday() -> None:
    assert age_at(_BIRTH, date(2025, 12, 31)) == 30
    assert age_at(_BIRTH, date(2026, 1, 1)) == 31


def test_openapi_exposes_own_scope_and_confirm_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "get" in paths[_API]
    assert "patch" in paths[_API + "/rascunho"]
    assert "201" in paths[_API + "/atualizacoes"]["post"]["responses"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_own_draft_completion_and_version_confirmation(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = _seed(sessions)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as client:

        async def login(email: str) -> str:
            client.cookies.clear()
            result = await client.post(
                "/api/v1/auth/login",
                json={"email": f"{email}@example.test", "senha": _PASSWORD},
            )
            assert result.status_code == 200
            return str(result.json()["csrf_token"])

        assert (await client.get(_API)).status_code == 401
        csrf = await login("cliente")
        assert (await client.get(_API)).json() == {"rascunho": None, "concluido": None}
        body = {
            "versao_base": None,
            "revisao": None,
            "dados": {"altura_cm": 175.2, "usa_medicamentos": None},
        }
        assert (await client.patch(_API + "/rascunho", json=body)).status_code == 403
        headers = {"X-CSRF-Token": csrf}
        partial = await client.patch(_API + "/rascunho", json=body, headers=headers)
        assert partial.status_code == 200
        draft = partial.json()
        assert draft["numero"] == 1 and draft["estado"] == "RASCUNHO"
        assert draft["dados"] == body["dados"]
        assert (await client.get(_API)).json()["rascunho"] == draft
        missing = await client.post(
            _API + "/conclusao",
            json={"versao_base": None, "revisao": draft["revisao"]},
            headers=headers,
        )
        assert missing.status_code == 422
        assert (await client.get(_API)).json()["rascunho"] == draft

        form = {**_FORM, "usa_medicamentos": "NAO_SEI", "altura_cm": 175.2}
        saved = await client.patch(
            _API + "/rascunho",
            json={"versao_base": None, "revisao": draft["revisao"], "dados": form},
            headers=headers,
        )
        assert saved.status_code == 200
        finished = await client.post(
            _API + "/conclusao",
            json={"versao_base": None, "revisao": saved.json()["revisao"]},
            headers=headers,
        )
        assert finished.status_code == 200
        previous = finished.json()
        assert previous["estado"] == "CONCLUIDO" and previous["numero"] == 1
        assert previous["dados"]["usa_medicamentos"] == "NAO_SEI"
        assert previous["concluido_por"] == str(people.client)
        assert previous["concluido_em"].endswith("Z")
        assert finished.headers["Cache-Control"] == "no-store"

        proposed = await client.patch(
            _API + "/rascunho",
            headers=headers,
            json={
                "versao_base": previous["id"],
                "revisao": None,
                "dados": {"peso_kg": 76.1},
            },
        )
        assert proposed.status_code == 200 and proposed.json()["numero"] == 2
        assert proposed.json()["dados"]["usa_medicamentos"] == "NAO_SEI"
        with sessions.begin() as db:
            assert is_current_snapshot(db, people.client, UUID(previous["id"]))

        change = {
            "versao_base": previous["id"],
            "revisao": proposed.json()["revisao"],
            "confirmado": False,
            "dados": proposed.json()["dados"],
        }
        assert (
            await client.post(_API + "/atualizacoes", json=change, headers=headers)
        ).status_code == 422
        confirm = await client.post(
            _API + "/atualizacoes",
            json={**change, "confirmado": True},
            headers=headers,
        )
        assert confirm.status_code == 201
        latest = confirm.json()
        assert latest["id"] != previous["id"] and latest["numero"] == 2
        assert latest["dados"]["peso_kg"] == 76.1
        old_path = _API + "/versoes/" + previous["id"]
        assert (await client.get(old_path)).json() == previous
        assert (await client.get(_API)).json() == {
            "rascunho": None,
            "concluido": latest,
        }
        stale = await client.post(
            _API + "/atualizacoes",
            json={**change, "confirmado": True},
            headers=headers,
        )
        assert stale.status_code == 409
        with sessions.begin() as db:
            assert not is_current_snapshot(db, people.client, UUID(previous["id"]))
            assert is_current_snapshot(db, people.client, UUID(latest["id"]))

        other_csrf = await login("outro")
        assert (await client.get(old_path)).status_code == 404
        assert (await client.get(_API)).json() == {"rascunho": None, "concluido": None}
        forged = await client.patch(
            _API + "/rascunho",
            json={**body, "cliente_id": str(people.client)},
            headers={"X-CSRF-Token": other_csrf},
        )
        assert forged.status_code == 422
        await login("instrutor")
        assert (await client.get(_API)).status_code == 403


@pytest.mark.database
def test_0006_keeps_snapshots_and_evaluations_immutable(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0005")
    command.upgrade(config, "head")
    command.check(config)
    factory = create_session_factory(connection)
    people = _seed(factory)
    with factory.begin() as session:
        draft = save_draft(
            session,
            people.client,
            people.client,
            DraftChange(
                versao_base=None, revisao=None, dados=DraftData.model_validate(_FORM)
            ),
        )
        with pytest.raises(OnboardingError):
            append_evaluation(session, people.client, people.instructor, draft.id, {})
        snapshot = complete_draft(
            session,
            people.client,
            people.client,
            Completion(versao_base=None, revisao=draft.revisao),
        )
        first = append_evaluation(
            session,
            people.client,
            people.instructor,
            snapshot.id,
            {"observacao": "sintética"},
        )
        second = append_evaluation(
            session, people.client, people.instructor, snapshot.id, {}
        )
        assert first.id != second.id and first.registrado_em <= second.registrado_em
        assert get_snapshot(session, people.other, snapshot.id) is None

    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(
            update(OnboardingVersion)
            .where(OnboardingVersion.id == snapshot.id)
            .values(dados={})
        )
    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(delete(Evaluation).where(Evaluation.id == first.id))
    with (
        pytest.raises(IntegrityError, match="fk_avaliacao_onboarding_cliente"),
        factory.begin() as session,
    ):
        session.add(
            Evaluation(
                id=uuid4(),
                cliente_id=people.other,
                instrutor_id=people.instructor,
                onboarding_id=snapshot.id,
                registrado_em=utc_now(),
                dados={},
            )
        )
    command.downgrade(config, "0005")
    assert not inspect(connection).has_table("onboarding_versao", schema="academia")
    assert inspect(connection).has_table("designacao", schema="academia")


@pytest.fixture
def isolated_sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    schema = "onb_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            yield create_session_factory(scoped)
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_concurrent_edits_cannot_replace_each_other(
    isolated_sessions: sessionmaker[Session],
) -> None:
    factory = isolated_sessions
    client = _seed(factory).client
    with factory.begin() as session:
        draft = save_draft(
            session,
            client,
            client,
            DraftChange(versao_base=None, revisao=None, dados=DraftData()),
        )
    barrier = Barrier(2)

    def edit(weight: float) -> int:
        barrier.wait(timeout=5)
        try:
            with factory.begin() as session:
                save_draft(
                    session,
                    client,
                    client,
                    DraftChange(
                        versao_base=None,
                        revisao=draft.revisao,
                        dados=DraftData(peso_kg=weight),
                    ),
                )
        except OnboardingError as exc:
            return exc.status
        return 200

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit, [75.1, 75.2])) == [200, 409]
    with factory.begin() as session:
        only = session.scalars(select(OnboardingVersion)).one()
        assert only.revision == 2 and only.dados["peso_kg"] in (75.1, 75.2)


def test_invitation_openapi_describes_restricted_json_and_staff_permissions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    schema = create_app().openapi()
    paths = schema["paths"]
    assert "201" in paths[_INVITES.format("{client_id}")]["post"]["responses"]
    assert "get" in paths[_INVITES.format("{client_id}")]
    assert "application/json" in paths[_TRADE]["post"]["requestBody"]["content"]
    assert "204" in paths[_COMPLETE]["post"]["responses"]
    properties = schema["components"]["schemas"]["RestrictedChange"]["properties"]
    assert set(properties) == {"revisao", "dados"}
    assert (
        schema["components"]["schemas"]["ExchangeRequest"]["properties"]["token"][
            "writeOnly"
        ]
        is True
    )


def _mailpit_token(email: str, invitation_id: str, expected_count: int) -> str:
    with httpx.Client(
        base_url="http://127.0.0.1:8025", trust_env=False, timeout=5
    ) as sink:
        result = sink.get("/api/v1/search", params={"query": f"to:{email}"})
        result.raise_for_status()
        messages = result.json()["messages"]
        assert len(messages) == expected_count
        [message] = [m for m in messages if m["MessageID"].startswith(invitation_id)]
        full = sink.get(f"/api/v1/message/{message['ID']}")
        full.raise_for_status()
    match = re.search(
        rf"{re.escape(_ORIGIN)}/onboarding/convite#token=([A-Za-z0-9_-]{{43}})",
        full.json()["Text"],
    )
    assert match is not None
    return match.group(1)


def _api(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> httpx.ASGITransport:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    return httpx.ASGITransport(
        app=create_app(
            identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
        )
    )


def _browser(transport: httpx.ASGITransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=transport, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
    )


async def _login(browser: httpx.AsyncClient, email: str) -> dict[str, str]:
    result = await browser.post(
        "/api/v1/auth/login", json={"email": email, "senha": _PASSWORD}
    )
    assert result.status_code == 200
    return {"X-CSRF-Token": result.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
async def test_invite_from_mailpit_resumes_and_completes_only_the_linked_draft(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    if environ.get("ACADEMIA_TEST_MAILPIT") != "1":
        pytest.skip("Inicie o Mailpit e configure ACADEMIA_TEST_MAILPIT=1.")
    suffix = "-" + uuid4().hex
    people = _seed(sessions, suffix)
    email = f"cliente{suffix}@example.test"
    api = _api(sessions, monkeypatch)
    invite_url = _INVITES.format(people.client)
    request_id = str(uuid4())
    async with (
        _browser(api) as staff,
        _browser(api) as guest,
        _browser(api) as another,
    ):
        assert (
            await guest.post(invite_url, json={"solicitacao_id": request_id})
        ).status_code == 401
        client_headers = await _login(another, f"outro{suffix}@example.test")
        assert (
            await another.post(
                invite_url, json={"solicitacao_id": request_id}, headers=client_headers
            )
        ).status_code == 403
        headers = await _login(staff, f"atendente{suffix}@example.test")
        assert (
            await staff.post(invite_url, json={"solicitacao_id": request_id})
        ).status_code == 403
        first = await staff.post(
            invite_url, json={"solicitacao_id": request_id}, headers=headers
        )
        assert first.status_code == 201
        result = first.json()
        assert result["estado"] == "ENVIADO"
        assert (await staff.get(invite_url)).json() == result
        replay = await staff.post(
            invite_url, json={"solicitacao_id": request_id}, headers=headers
        )
        assert replay.json() == result
        token = await to_thread(_mailpit_token, email, result["id"], 1)

        assert (
            await guest.post(
                _TRADE,
                json={"token": token},
                headers={"Origin": "https://externo.example.test"},
            )
        ).status_code == 403
        assert (await guest.post(_TRADE, json={"token": "inválido"})).status_code == 401
        forged = await guest.post(
            _TRADE, json={"token": token, "cliente_id": str(people.other)}
        )
        assert forged.status_code == 422 and token not in forged.text
        exchanged = await guest.post(_TRADE, json={"token": token})
        assert exchanged.status_code == 200 and token not in exchanged.text
        assert exchanged.json()["expira_em"] == result["expira_em"]
        cookie = exchanged.headers["Set-Cookie"].lower()
        assert all(
            part in cookie
            for part in (
                "httponly",
                "secure",
                "samesite=lax",
                f"path={RESTRICTED_PATH}",
            )
        )
        secret = guest.cookies[RESTRICTED_COOKIE]
        assert secret != token
        assert (await another.post(_TRADE, json={"token": token})).status_code == 401
        assert (await guest.get("/api/v1/auth/session")).status_code == 401
        assert (await guest.get(_API)).status_code == 401
        assert (await guest.get(invite_url)).status_code == 401
        draft = (await guest.get(_DRAFT)).json()
        assert draft["dados"] == {} and draft["numero"] == 1
        patch = {"revisao": draft["revisao"], "dados": {"altura_cm": 175}}
        assert (
            await guest.patch(
                _DRAFT, json=patch, headers={"Origin": "https://externo.example.test"}
            )
        ).status_code == 403
        assert (
            await guest.post(_COMPLETE, json={"revisao": draft["revisao"]})
        ).status_code == 422
        saved = await guest.patch(_DRAFT, json=patch)
        assert saved.status_code == 200
        assert (await guest.get(_DRAFT)).json() == saved.json()
        assert (await another.get(_API)).json() == {"rascunho": None, "concluido": None}
        with sessions.begin() as session:
            row = session.get(OnboardingInvitation, UUID(result["id"]))
            assert row is not None
            assert row.token_hash == digest(token)
            assert row.sessao_restrita_hash == digest(secret)
            assert row.onboarding_id == UUID(draft["id"])

        next_invite = await staff.post(
            invite_url, json={"solicitacao_id": str(uuid4())}, headers=headers
        )
        assert (
            next_invite.status_code == 201 and next_invite.json()["estado"] == "ENVIADO"
        )
        assert (await guest.get(_DRAFT)).status_code == 401
        assert (await guest.post(_TRADE, json={"token": token})).status_code == 401
        new_token = await to_thread(_mailpit_token, email, next_invite.json()["id"], 2)
        assert (await guest.post(_TRADE, json={"token": new_token})).status_code == 200
        assert (await guest.get(_DRAFT)).json() == saved.json()
        final = await guest.patch(
            _DRAFT, json={"revisao": saved.json()["revisao"], "dados": _FORM}
        )
        assert final.status_code == 200
        finished = await guest.post(
            _COMPLETE, json={"revisao": final.json()["revisao"]}
        )
        assert finished.status_code == 204 and RESTRICTED_COOKIE not in guest.cookies
        assert (await guest.get(_DRAFT)).status_code == 401
        await _login(guest, email)
        completed = (await guest.get(_API)).json()["concluido"]
        assert completed["id"] == draft["id"]
        assert completed["concluido_por"] == str(people.client)
        assert (
            await staff.post(
                invite_url, json={"solicitacao_id": str(uuid4())}, headers=headers
            )
        ).status_code == 409
    assert token not in caplog.text and secret not in caplog.text


@pytest.mark.integration
@pytest.mark.anyio
async def test_invite_smtp_failure_persists_and_does_not_complete_onboarding(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = _seed(sessions)
    # Porta reservada pelo próprio teste, sem escuta SMTP.
    from socket import socket

    with socket() as unavailable:
        unavailable.bind(("127.0.0.1", 0))
        monkeypatch.setenv("ACADEMIA_SMTP_PORT", str(unavailable.getsockname()[1]))
        async with _browser(_api(sessions, monkeypatch)) as staff:
            headers = await _login(staff, "atendente@example.test")
            path = _INVITES.format(people.client)
            key = {"solicitacao_id": str(uuid4())}
            result = await staff.post(path, json=key, headers=headers)
            assert result.status_code == 201 and result.json()["estado"] == "FALHOU"
            assert (await staff.get(path)).json() == result.json()
            assert (
                await staff.post(path, json=key, headers=headers)
            ).json() == result.json()
            for _ in range(2):
                assert (
                    await staff.post(
                        path, json={"solicitacao_id": str(uuid4())}, headers=headers
                    )
                ).status_code == 201
            assert (
                await staff.post(
                    path, json={"solicitacao_id": str(uuid4())}, headers=headers
                )
            ).status_code == 429
    with sessions.begin() as session:
        notifications = session.scalars(
            select(Notification).where(
                Notification.tipo == EmailKind.CONVITE_ONBOARDING
            )
        ).all()
        assert len(notifications) == 3
        assert all(
            n.estado == DeliveryState.FALHOU and n.tentativas == 1
            for n in notifications
        )
        version = session.scalars(select(OnboardingVersion)).one()
        assert version.estado == "RASCUNHO" and version.concluido_em is None


@pytest.mark.integration
@pytest.mark.anyio
async def test_expired_invite_and_other_credential_are_refused(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = _seed(sessions)
    with sessions.begin() as session:
        invite_id, mail = issue_invitation(
            session, people.client, people.attendant, uuid4()
        )
        assert mail is not None
        row = session.get(OnboardingInvitation, invite_id)
        assert row is not None
        row.expira_em = utc_now() - timedelta(seconds=1)
        user = session.get(User, people.other)
        assert user is not None
        user.estado = AccountState.CONVIDADO
        session.flush()
        first_access = issue_first_access(session, people.other, now=utc_now())

    async with _browser(_api(sessions, monkeypatch)) as guest:
        for token in (mail.token, first_access.token):
            assert (await guest.post(_TRADE, json={"token": token})).status_code == 401
            assert RESTRICTED_COOKIE not in guest.cookies

        with sessions.begin() as session:
            invite_id, mail = issue_invitation(
                session, people.other, people.attendant, uuid4()
            )
            assert mail is not None
        assert (await guest.post(_TRADE, json={"token": mail.token})).status_code == 200
        assert (await guest.get(_DRAFT)).status_code == 200
        with sessions.begin() as session:
            row = session.get(OnboardingInvitation, invite_id)
            assert row is not None and row.consumido_em is not None
            # Avança o relógio da API sem criar um estado inválido no banco.
            future = row.expira_em + timedelta(seconds=1)
        monkeypatch.setattr(
            "app.modules.onboarding.invitations.utc_now", lambda: future
        )
        assert (await guest.get(_DRAFT)).status_code == 401


@pytest.mark.integration
def test_reissue_revokes_unused_link_and_concurrent_exchange_consumes_once(
    isolated_sessions: sessionmaker[Session],
) -> None:
    factory = isolated_sessions
    people = _seed(factory)
    with factory.begin() as session:
        _, previous = issue_invitation(
            session, people.client, people.attendant, uuid4()
        )
        assert previous is not None
    with factory.begin() as session:
        invite_id, current = issue_invitation(
            session, people.client, people.attendant, uuid4()
        )
        assert current is not None
    with factory.begin() as session:
        with pytest.raises(OnboardingError) as rejected:
            exchange_invitation(session, previous.token)
        assert rejected.value.status == 401

    token = current.token
    barrier = Barrier(2)

    def exchange() -> str | None:
        barrier.wait(timeout=5)
        try:
            with factory.begin() as session:
                secret, _ = exchange_invitation(session, token)
        except OnboardingError as exc:
            assert exc.status == 401
            return None
        return secret

    with ThreadPoolExecutor(max_workers=2) as pool:
        attempts = [pool.submit(exchange) for _ in range(2)]
        [successful] = [secret for attempt in attempts if (secret := attempt.result())]
    with factory.begin() as session:
        stored = session.get(OnboardingInvitation, invite_id)
        assert stored is not None and stored.sessao_restrita_hash == digest(successful)


@pytest.mark.database
def test_0007_enforces_invite_constraints_and_downgrades_without_erasing_draft(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0006")
    factory = create_session_factory(connection)
    people = _seed(factory)
    with factory.begin() as session:
        draft = save_draft(
            session,
            people.client,
            people.client,
            DraftChange(versao_base=None, revisao=None, dados=DraftData(altura_cm=170)),
        )

    command.upgrade(config, "0007")
    with factory.begin() as session:
        _, issued = issue_invitation(session, people.client, people.attendant, uuid4())
        assert issued is not None
    with (
        pytest.raises(IntegrityError, match="uq_convite_onboarding_nao_revogado"),
        factory.begin() as session,
    ):
        session.add(
            OnboardingInvitation(
                id=uuid4(),
                onboarding_id=draft.id,
                token_hash=digest("outro"),
                expira_em=utc_now() + timedelta(hours=1),
            )
        )
    with (
        pytest.raises(IntegrityError, match="ck_convite_onboarding_sessao"),
        factory.begin() as session,
    ):
        session.execute(
            update(OnboardingInvitation).values(sessao_restrita_hash=digest("isolado"))
        )
    command.downgrade(config, "0006")
    assert not inspect(connection).has_table("convite_onboarding", schema="academia")
    with factory.begin() as session:
        row = session.get(OnboardingVersion, draft.id)
        assert row is not None and row.dados == {"altura_cm": 170.0}


_ASSESSMENTS = "/api/v1/onboarding/clientes/{client_id}/avaliacoes"


def test_assessment_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    openapi = create_app().openapi()
    routes = openapi["paths"][_ASSESSMENTS]
    assert "200" in routes["get"]["responses"]
    assert "201" in routes["post"]["responses"]
    request = openapi["components"]["schemas"]["CreateAssessment"]
    assert set(request["required"]) == {"onboarding_id", "solicitacao_id", "observacao"}
    assert request["additionalProperties"] is False
    for invalid in (" ", "x" * 1001):
        with pytest.raises(ValueError):
            CreateAssessment(
                onboarding_id=uuid4(), solicitacao_id=uuid4(), observacao=invalid
            )


def _finish_initial(session: Session, client_id: UUID) -> SnapshotView:
    draft = save_draft(
        session,
        client_id,
        client_id,
        DraftChange(
            versao_base=None, revisao=None, dados=DraftData.model_validate(_FORM)
        ),
    )
    return complete_draft(
        session,
        client_id,
        client_id,
        Completion(versao_base=None, revisao=draft.revisao),
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_assessment_transfer_preserves_authorship_and_revokes_old_access(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    people = _seed(sessions)
    with sessions.begin() as session:
        snapshot = _finish_initial(session, people.client)
        other_snapshot = _finish_initial(session, people.other)
    api = _api(sessions, monkeypatch)
    endpoint = _ASSESSMENTS.format(client_id=people.client)
    link = f"/api/v1/designacoes/clientes/{people.client}"
    initial_note = {
        "onboarding_id": str(snapshot.id),
        "solicitacao_id": str(uuid4()),
        "observacao": "Primeiro registro sintético",
    }
    async with (
        _browser(api) as admin,
        _browser(api) as old,
        _browser(api) as new,
        _browser(api) as visitor,
    ):
        assert (await visitor.get(endpoint)).status_code == 401
        staff_headers = await _login(visitor, "atendente@example.test")
        assert (await visitor.get(endpoint)).status_code == 403
        assert (
            await visitor.post(endpoint, json=initial_note, headers=staff_headers)
        ).status_code == 403
        admin_headers = await _login(admin, "admin@example.test")
        assert (await admin.get(endpoint)).status_code == 403
        old_headers = await _login(old, "instrutor@example.test")
        new_headers = await _login(new, "substituto@example.test")
        assert (await old.get(endpoint)).status_code == 403

        assigned = await admin.put(
            link,
            headers=admin_headers,
            json={"instrutor_id": str(people.instructor), "vigente_id": None},
        )
        assert assigned.status_code == 200
        assert (await new.get(endpoint)).status_code == 403
        initial = await old.get(endpoint)
        assert initial.status_code == 200
        assert initial.headers["Cache-Control"] == "no-store"
        assert initial.json()["snapshot"]["id"] == str(snapshot.id)
        assert initial.json()["historico"]["total"] == 0
        assert (await old.post(endpoint, json=initial_note)).status_code == 403

        forged = await old.post(
            endpoint,
            headers=old_headers,
            json={**initial_note, "instrutor_id": str(people.admin)},
        )
        assert (
            forged.status_code == 422 and initial_note["observacao"] not in forged.text
        )
        unrelated = await old.post(
            endpoint,
            headers=old_headers,
            json={**initial_note, "onboarding_id": str(other_snapshot.id)},
        )
        assert unrelated.status_code == 404
        first = await old.post(endpoint, headers=old_headers, json=initial_note)
        assert first.status_code == 201 and first.headers["Cache-Control"] == "no-store"
        assert first.json()["instrutor_id"] == str(people.instructor)
        assert first.json()["registrado_em"].endswith("Z")
        repeat = await old.post(endpoint, headers=old_headers, json=initial_note)
        assert repeat.status_code == 201 and repeat.json() == first.json()
        assert (
            await old.post(
                endpoint,
                headers=old_headers,
                json={**initial_note, "observacao": "Alterada"},
            )
        ).status_code == 409

        transfer = await admin.put(
            link,
            headers=admin_headers,
            json={
                "instrutor_id": str(people.replacement),
                "vigente_id": assigned.json()["id"],
            },
        )
        assert transfer.status_code == 200
        assert (await old.get("/api/v1/auth/session")).status_code == 200
        assert (await old.get(endpoint)).status_code == 403
        assert (
            await old.post(endpoint, headers=old_headers, json=initial_note)
        ).status_code == 403

        with sessions.begin() as session:
            updated = confirm_update(
                session,
                people.client,
                people.client,
                ConfirmUpdate(
                    versao_base=snapshot.id,
                    confirmado=True,
                    dados=OnboardingData.model_validate({**_FORM, "altura_cm": 178}),
                ),
            )
        second_note = {
            **initial_note,
            "solicitacao_id": str(uuid4()),
            "observacao": "Segundo registro sintético",
        }
        assert (
            await new.post(endpoint, headers=new_headers, json=second_note)
        ).status_code == 409
        second = await new.post(
            endpoint,
            headers=new_headers,
            json={**second_note, "onboarding_id": str(updated.id)},
        )
        assert second.status_code == 201 and second.json()["instrutor_id"] == str(
            people.replacement
        )
        assert second.json()["registrado_em"] >= first.json()["registrado_em"]
        history = await new.get(endpoint + "?limite=1")
        assert history.json()["historico"]["total"] == 2
        assert history.json()["historico"]["itens"] == [second.json()]
        previous = await new.get(endpoint + "?pagina=2&limite=1")
        assert previous.json()["historico"]["itens"] == [first.json()]
        assert first.json()["instrutor_nome"] == "instrutor"
        assert second.json()["instrutor_nome"] == "substituto"


@pytest.mark.integration
def test_ai_assessment_context_requires_own_current_snapshot_and_never_mixes_clients(
    sessions: sessionmaker[Session],
) -> None:
    people = _seed(sessions)
    with sessions.begin() as session:
        own = _finish_initial(session, people.client)
        other = _finish_initial(session, people.other)
        append_evaluation(
            session,
            people.other,
            people.instructor,
            other.id,
            {"observacao": "Somente B"},
        )
        session.flush()
        actor = Actor(people.client, frozenset({Role.CLIENTE}))
        empty = read_assessment_context(session, actor, people.client, own.id)
        assert empty.avaliacao_id is None and empty.observacao_avaliacao is None
        for target, reference, expected in (
            (people.other, other.id, 403),
            (people.client, other.id, 404),
        ):
            with pytest.raises(OnboardingError) as error:
                read_assessment_context(session, actor, target, reference)
            assert error.value.status == expected

        staff = Actor(people.instructor, frozenset({Role.INSTRUTOR}))
        admin = Actor(people.admin, frozenset({Role.ADMINISTRADOR}))
        change_assignment(
            session,
            people.client,
            ChangeAssignment(
                instrutor_id=people.instructor,
                vigente_id=None,
            ),
            admin,
            uuid4(),
        )
        with pytest.raises(OnboardingError) as rejected:
            read_assessment_context(session, staff, people.client, own.id)
        assert rejected.value.status == 403

        row = append_evaluation(
            session,
            people.client,
            people.instructor,
            own.id,
            {"observacao": "Somente A"},
        )
        session.flush()
        data = read_assessment_context(session, actor, people.client, own.id)
        assert data.avaliacao_id == row.id and data.observacao_avaliacao == "Somente A"
        assert "Somente B" not in data.model_dump_json()
        assert {"cliente_id", "instrutor_id", "criado_por"}.isdisjoint(
            data.model_dump()
        )

        updated = confirm_update(
            session,
            people.client,
            people.client,
            ConfirmUpdate(
                versao_base=own.id,
                confirmado=True,
                dados=OnboardingData.model_validate(_FORM),
            ),
        )
        session.flush()
        assert (
            read_assessment_context(
                session, actor, people.client, updated.id
            ).avaliacao_id
            is None
        )
        with pytest.raises(OnboardingError) as stale:
            read_assessment_context(session, actor, people.client, own.id)
        assert stale.value.status == 409

import socket
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from sqlite3 import OperationalError
from threading import Thread
from time import monotonic, sleep
from uuid import UUID, uuid4

import httpx
import pytest
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.testclient import TestClient
from simulators.turnstile.contracts import CALLBACK_PATH, Command, Passage, Settings
from simulators.turnstile.http import create_app
from simulators.turnstile.store import RejectedOperation, Store

COMMAND_TOKEN = "sintetico_comando_acs07_para_testes"
CALLBACK_TOKEN = "sintetico_retorno_acs07_para_testes"
AUTH = {"Authorization": "Bearer " + COMMAND_TOKEN}
NOW = datetime(2026, 11, 24, 12, tzinfo=UTC)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    config = Settings.model_validate(
        {
            "command_token": COMMAND_TOKEN,
            "callback_token": CALLBACK_TOKEN,
            "store_path": tmp_path / "turnstile.sqlite3",
            "fault": "NONE",
        }
    )
    Store(config.store_path).prepare()
    return config


def command_payload(**fields: object) -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": str(uuid4()),
        "access_decision_id": str(uuid4()),
        "direction": "ENTRY",
        "decision": "ALLOW",
        "expires_at": (NOW + timedelta(seconds=20)).isoformat(),
        "client_id": str(uuid4()),
        **fields,
    }


def passage_payload() -> dict[str, object]:
    return {"schema_version": 1, "event_id": str(uuid4())}


def passage_route(command: dict[str, object]) -> str:
    return f"/commands/{command['request_id']}/passages"


@pytest.mark.parametrize(
    "changes",
    [
        {"callback_token": COMMAND_TOKEN},
        {"url": "http://0.0.0.0:8011"},
        {"callback_url": "https://example.test" + CALLBACK_PATH},
        {"callback_url": "http://127.0.0.1:8000/outra-rota"},
        {"callback_url": "http://127.0.0.1:8000" + CALLBACK_PATH + "?token=1"},
    ],
)
def test_configuration_rejects_unsafe_values(changes: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        Settings.model_validate(
            {
                "command_token": COMMAND_TOKEN,
                "callback_token": CALLBACK_TOKEN,
                **changes,
            }
        )


def test_store_preparation_is_explicit_and_keeps_existing_commands(
    tmp_path: Path,
) -> None:
    path = tmp_path / "novo.sqlite3"
    store = Store(path)
    with pytest.raises(OperationalError, match="unable to open database file"):
        store.verify()
    assert not path.exists()
    store.prepare()
    store.verify()
    command = Command.model_validate(command_payload())
    assert store.accept(command, NOW)
    store.prepare()
    assert not Store(path).accept(command, NOW)


def test_concurrent_command_replay_returns_one_first_receipt(
    settings: Settings,
) -> None:
    command = Command.model_validate(command_payload())
    store = Store(settings.store_path)
    with ThreadPoolExecutor(max_workers=2) as jobs:
        first = jobs.submit(store.accept, command, NOW)
        second = jobs.submit(store.accept, command, NOW)
        assert sorted((first.result(timeout=10), second.result(timeout=10))) == [
            False,
            True,
        ]


def test_api_accepts_and_replays_without_creating_passage(settings: Settings) -> None:
    delivered: list[Passage] = []
    with TestClient(
        create_app(settings, clock=lambda: NOW, delivery=delivered.append)
    ) as api:
        spec = api.get("/openapi.json").json()
        assert spec["paths"]["/commands"]["post"]["security"] == [
            {"ComandoCatraca": []}
        ]
        assert {"200", "202", "409", "410"} <= set(
            spec["paths"]["/commands"]["post"]["responses"]
        )
        command = command_payload()
        assert api.post("/commands", json=command).status_code == 401
        assert (
            api.post(
                "/commands",
                json=command,
                headers={"Authorization": "Bearer " + CALLBACK_TOKEN},
            ).status_code
            == 401
        )
        assert (
            api.post(
                "/commands",
                content="{",
                headers=AUTH
                | {
                    "Content-Type": "application/json",
                },
            ).status_code
            == 422
        )
        for extra in (
            {"schema_version": True},
            {"direction": "OTHER"},
            {"expires_at": "2026-11-24T12:00:20"},
            {"callback_url": "http://127.0.0.1:8080" + CALLBACK_PATH},
        ):
            assert (
                api.post("/commands", json=command | extra, headers=AUTH).status_code
                == 422
            )
        accepted = api.post("/commands", json=command, headers=AUTH)
        assert accepted.status_code == 202
        replay = api.post(
            "/commands",
            json=command
            | {
                "expires_at": "2026-11-24T09:00:20-03:00",
            },
            headers=AUTH,
        )
        assert replay.status_code == 200 and replay.json() == accepted.json()
        assert accepted.json() == {
            "schema_version": 1,
            "request_id": command["request_id"],
            "status": "ACCEPTED",
        }
        assert (
            api.post(
                "/commands", json=command | {"decision": "DENY"}, headers=AUTH
            ).status_code
            == 409
        )
        assert delivered == []
        trigger = passage_payload()
        assert api.post(passage_route(command), json=trigger).status_code == 401
        first = api.post(passage_route(command), json=trigger, headers=AUTH)
        assert first.status_code == 201
        duplicate = api.post(passage_route(command), json=trigger, headers=AUTH)
        assert duplicate.status_code == 200 and duplicate.json() == first.json()
        assert len(delivered) == 1 and delivered[0].simulated
        assert (
            api.post(
                passage_route(command), json=passage_payload(), headers=AUTH
            ).status_code
            == 409
        )
        other_command = command_payload()
        assert (
            api.post("/commands", json=other_command, headers=AUTH).status_code == 202
        )
        assert (
            api.post(
                passage_route(other_command), json=trigger, headers=AUTH
            ).status_code
            == 409
        )

    with TestClient(create_app(settings, clock=lambda: NOW)) as reopened:
        same = reopened.post(passage_route(command), json=trigger, headers=AUTH)
        assert same.status_code == 200 and same.json() == first.json()


def test_refused_expired_and_unknown_commands_cannot_return(settings: Settings) -> None:
    start = NOW
    received: list[Passage] = []
    with TestClient(
        create_app(settings, clock=lambda: start, delivery=received.append)
    ) as api:
        forbidden = command_payload(decision="DENY", client_id=None)
        expired = command_payload(expires_at=NOW.isoformat())
        allow = command_payload()
        assert api.post("/commands", json=expired, headers=AUTH).status_code == 410
        assert api.post("/commands", json=forbidden, headers=AUTH).status_code == 202
        assert api.post("/commands", json=allow, headers=AUTH).status_code == 202
        denied = api.post(
            passage_route(forbidden), json=passage_payload(), headers=AUTH
        )
        assert denied.status_code == 409 and denied.json()["detail"] == "COMMAND_DENIED"
        assert (
            api.post(
                passage_route(command_payload()), json=passage_payload(), headers=AUTH
            ).status_code
            == 404
        )
        start += timedelta(seconds=20)
        assert (
            api.post(
                passage_route(allow), json=passage_payload(), headers=AUTH
            ).status_code
            == 410
        )
        assert received == []


@contextmanager
def live_server(app: FastAPI) -> Iterator[str]:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        host, port = listener.getsockname()
        server = uvicorn.Server(
            uvicorn.Config(app, access_log=False, lifespan="off", log_level="warning")
        )
        task = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        task.start()
        try:
            deadline = monotonic() + 10
            while not server.started and task.is_alive() and monotonic() < deadline:
                sleep(0.02)
            assert server.started
            yield f"http://{host}:{port}"
        finally:
            server.should_exit = True
            task.join(timeout=10)
            assert not task.is_alive()


@pytest.mark.integration
def test_real_http_callback_preserves_identity_after_an_uncertain_timeout(
    settings: Settings,
) -> None:
    receiver = FastAPI()
    arrivals: list[Passage] = []
    callback_mode = "timeout"
    confirmed: dict[UUID, Passage] = {}

    @receiver.post(CALLBACK_PATH)
    def receive_passage(
        data: Passage,
        response: Response,
        authorization: str = Header(),
    ) -> dict[str, object]:
        if authorization != "Bearer " + CALLBACK_TOKEN:
            raise HTTPException(401)
        arrivals.append(data)
        if callback_mode == "wrong_id":
            response.status_code = 201
            return {"schema_version": 1, "event_id": str(uuid4()), "status": "RECORDED"}
        duplicate = data.event_id in confirmed
        if duplicate:
            assert confirmed[data.event_id] == data
        else:
            confirmed[data.event_id] = data
        response.status_code = 200 if duplicate else 201
        if callback_mode == "timeout":
            sleep(0.6)
        return {
            "schema_version": 1,
            "event_id": str(data.event_id),
            "status": "RECORDED",
        }

    current = NOW
    with live_server(receiver) as callback:
        config = settings.model_copy(
            update={
                "callback_url": callback + CALLBACK_PATH,
                "callback_timeout_seconds": 0.2,
            }
        )
        with (
            live_server(create_app(config, clock=lambda: current)) as url,
            httpx.Client(
                base_url=url,
                headers=AUTH,
                trust_env=False,
                timeout=3,
            ) as api,
        ):
            allow = command_payload(direction="EXIT")
            assert api.post("/commands", json=allow).status_code == 202
            assert api.post("/commands", json=allow).status_code == 200
            deny = command_payload(decision="DENY")
            assert api.post("/commands", json=deny).status_code == 202
            assert (
                api.post(passage_route(deny), json=passage_payload()).status_code == 409
            )
            assert arrivals == []

            trigger = passage_payload()
            timeout = api.post(passage_route(allow), json=trigger)
            assert (
                timeout.status_code == 504
                and timeout.json()["detail"] == "CALLBACK_TIMEOUT"
            )
            callback_mode = "wrong_id"
            current += timedelta(seconds=25)
            invalid = api.post(passage_route(allow), json=trigger)
            assert invalid.status_code == 502
            callback_mode = "normal"
            receipt = api.post(passage_route(allow), json=trigger)
            assert receipt.status_code == 201 and receipt.json()["simulated"]
            assert api.post(passage_route(allow), json=trigger).status_code == 200
            assert len(arrivals) == 3 and len(confirmed) == 1
            event = arrivals[0]
            assert all(item == event for item in arrivals)
            assert (
                event.occurred_at == NOW
                and event.direction == "EXIT"
                and event.simulated
            )


@pytest.mark.integration
def test_callback_distinguishes_expiry_from_temporary_failure(
    settings: Settings,
) -> None:
    receiver = FastAPI()
    arrivals: list[Passage] = []
    current = NOW

    @receiver.post(CALLBACK_PATH)
    def receive_passage(data: Passage) -> None:
        arrivals.append(data)
        raise HTTPException(410 if current >= NOW + timedelta(seconds=20) else 503)

    with live_server(receiver) as callback:
        config = settings.model_copy(update={"callback_url": callback + CALLBACK_PATH})
        with TestClient(create_app(config, clock=lambda: current)) as api:
            command = command_payload()
            trigger = passage_payload()
            assert api.post("/commands", json=command, headers=AUTH).status_code == 202
            unavailable = api.post(passage_route(command), json=trigger, headers=AUTH)
            assert unavailable.status_code == 502
            current += timedelta(seconds=21)
            expired = api.post(passage_route(command), json=trigger, headers=AUTH)
            assert expired.status_code == 410
            assert expired.json()["detail"] == "CALLBACK_EXPIRED"
            assert len(arrivals) == 2 and arrivals[0] == arrivals[1]


@pytest.mark.integration
@pytest.mark.parametrize(("mode", "status"), [("TIMEOUT", 504), ("UNAVAILABLE", 503)])
def test_real_http_fault_does_not_accept_a_command(
    settings: Settings,
    mode: str,
    status: int,
) -> None:
    command = command_payload()
    faulted = settings.model_copy(update={"fault": mode})
    with (
        live_server(create_app(faulted, clock=lambda: NOW)) as url,
        httpx.Client(
            base_url=url,
            headers=AUTH,
            trust_env=False,
            timeout=2,
        ) as api,
    ):
        assert api.post("/commands", json=command).status_code == status
    with (
        live_server(create_app(settings, clock=lambda: NOW)) as url,
        httpx.Client(
            base_url=url,
            headers=AUTH,
            trust_env=False,
            timeout=2,
        ) as api,
    ):
        assert (
            api.post(passage_route(command), json=passage_payload()).status_code == 404
        )
        assert api.post("/commands", json=command).status_code == 202


@pytest.mark.integration
def test_restart_keeps_original_passage_when_the_receiver_is_down(
    settings: Settings,
) -> None:
    command = command_payload()
    trigger = passage_payload()
    received: list[Passage] = []

    def reject(event: Passage) -> None:
        received.append(event)
        raise RejectedOperation(502, "CALLBACK_UNAVAILABLE")

    with (
        live_server(create_app(settings, clock=lambda: NOW, delivery=reject)) as url,
        httpx.Client(base_url=url, headers=AUTH, trust_env=False, timeout=3) as api,
    ):
        assert api.post("/commands", json=command).status_code == 202
        assert api.post(passage_route(command), json=trigger).status_code == 502

    with (
        live_server(
            create_app(
                settings,
                clock=lambda: NOW + timedelta(minutes=1),
                delivery=received.append,
            )
        ) as url,
        httpx.Client(base_url=url, headers=AUTH, trust_env=False, timeout=3) as api,
    ):
        assert api.post(passage_route(command), json=trigger).status_code == 201
        assert api.post(passage_route(command), json=trigger).status_code == 200

    assert len(received) == 2 and received[0] == received[1]
    assert received[0].occurred_at == NOW and received[0].simulated


@pytest.mark.integration
def test_concurrent_distinct_events_allow_only_one_passage_per_command(
    settings: Settings,
) -> None:
    received: list[Passage] = []
    command = command_payload()
    with live_server(
        create_app(settings, clock=lambda: NOW, delivery=received.append)
    ) as url:
        with httpx.Client(
            base_url=url, headers=AUTH, trust_env=False, timeout=3
        ) as api:
            assert api.post("/commands", json=command).status_code == 202

            def submit(event: dict[str, object]) -> int:
                return api.post(passage_route(command), json=event).status_code

            with ThreadPoolExecutor(max_workers=2) as jobs:
                statuses = list(
                    jobs.map(submit, [passage_payload(), passage_payload()])
                )

    assert sorted(statuses) == [201, 409]
    assert len(received) == 1

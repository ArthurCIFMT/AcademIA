"""Jornada de acesso com Edge, PostgreSQL e simulador HTTP isolados."""

import os
import secrets
import shutil
import subprocess
from base64 import b64decode
from datetime import UTC, datetime
from pathlib import Path
from socket import socket
from uuid import uuid4

import pytest
from simulators.turnstile.contracts import Settings
from simulators.turnstile.http import create_app as create_simulator
from simulators.turnstile.store import Store
from sqlalchemy import Connection

from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.access.biometrics.models import FacialReference
from app.modules.access.biometrics.provider import FaceCandidate
from app.modules.identity.settings import AuthSettings
from tests.acceptance.__main__ import SerializedHTTP
from tests.acceptance.fixtures import seed_people
from tests.access.test_authorization import RETURN_URL, serve
from tests.access.test_facial_reference import _solid
from tests.access.test_identification import RecognitionDouble
from tests.ai.evaluation.reporting import write_json

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("ACADEMIA_E2E_ACCESS") != "1", reason="Ensaio Edge opt-in"
)
def test_edge_access_journey(
    migration: Connection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    node = os.environ.get("ACADEMIA_E2E_NODE") or shutil.which("node")
    assert node and subprocess.check_output([node, "--version"], text=True).startswith(
        "v24."
    )
    with socket() as probe:
        probe.bind(("127.0.0.1", 0))
        origin = f"http://127.0.0.1:{probe.getsockname()[1]}"

    password, suffix = secrets.token_urlsafe(24), secrets.token_hex(4)
    command_token, callback_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    sessions = create_session_factory(migration)
    people, users = seed_people(sessions, password, suffix)
    subject = "referencia-facial-sintetica"
    with sessions.begin() as db:
        db.add(
            FacialReference(
                id=uuid4(),
                cliente_id=people["seguranca"].user_id,
                subject_externo=subject,
                image_id=str(uuid4()),
                estado="ATIVA",
                cadastrada_por=people["atendente"].user_id,
                criada_em=datetime.now(UTC),
            )
        )
    provider = RecognitionDouble()
    provider.candidates = [FaceCandidate(subject=subject, similarity=0.99)]
    fixture = tmp_path / "fixture-privada.json"
    write_json(fixture, {"usuarios": users, "sufixo": suffix})
    photo = tmp_path / "sintetica.jpg"
    photo.write_bytes(b64decode(_solid()))

    config = Settings.model_validate(
        {
            "store_path": tmp_path / "turnstile.sqlite3",
            "command_token": command_token,
            "callback_token": callback_token,
            "callback_url": origin + RETURN_URL,
        }
    )
    Store(config.store_path).prepare()
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ACADEMIA_TURNSTILE_COMMAND_TOKEN", command_token)
    monkeypatch.setenv("ACADEMIA_TURNSTILE_CALLBACK_TOKEN", callback_token)
    monkeypatch.setenv("ACADEMIA_ACCESS_MODALIDADE_PONTO", "Musculação")
    monkeypatch.setenv("ACADEMIA_ACCESS_COMMAND_TTL_SECONDS", "120")
    with serve(lambda _: create_simulator(config)) as turnstile:
        monkeypatch.setenv("ACADEMIA_TURNSTILE_URL", turnstile)
        app = create_app(
            identity_sessions=sessions,
            auth_settings=AuthSettings(origin=origin, allow_local_http=True),
            biometrics_provider=provider,
        )
        app.add_middleware(SerializedHTTP)
        with serve(lambda _: app) as backend:
            env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith(("ACADEMIA_", "GROQ_", "GEMINI_", "MP_", "VITE_"))
            } | {
                "ACADEMIA_E2E_ORIGIN": origin,
                "ACADEMIA_E2E_API": backend,
                "ACADEMIA_E2E_FIXTURE": str(fixture),
                "ACADEMIA_E2E_PASSWORD": password,
                "ACADEMIA_E2E_CHANNEL": "msedge",
                "ACADEMIA_E2E_OUTPUT": str(tmp_path),
                "ACADEMIA_E2E_ACCESS_PHOTO": str(photo),
                "ACADEMIA_E2E_ACCESS_SIMULATOR": turnstile,
                "ACADEMIA_E2E_ACCESS_TOKEN": command_token,
                "VITE_API_BASE_URL": "/api",
            }
            env["PATH"] = (
                str(Path(node).resolve().parent) + os.pathsep + env.get("PATH", "")
            )
            run = subprocess.run(
                [
                    node,
                    "node_modules/@playwright/test/cli.js",
                    "test",
                    "--config",
                    "tests/e2e/playwright.access.config.ts",
                ],
                cwd=ROOT / "frontend",
                env=env,
                capture_output=True,
                timeout=160,
            )
    assert run.returncode == 0, run.stdout.decode("utf-8", errors="replace")
    assert provider.calls == 2
    print(run.stdout.decode("utf-8", errors="replace"))

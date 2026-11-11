from uuid import uuid4

import httpx
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.main import create_app
from app.modules.identity.settings import AuthSettings
from tests.ai.test_generation import Scenario
from tests.ai.test_generation import scenario as scenario
from tests.ai.test_triage_integration import ORIGIN, PASSWORD
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.integration
@pytest.mark.anyio
async def test_real_rest_generation_authorization_csrf_and_replay(
    sessions: sessionmaker[Session], scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, service, provider = scenario
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    monkeypatch.setattr("app.modules.ai.http.GenerationService", lambda _: service)
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )
    path = "/api/v1/ia/fichas/execucoes"
    id = str(uuid4())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=ORIGIN,
        headers={"Origin": ORIGIN},
    ) as client:
        assert (await client.post(path, json={"solicitacao_id": id})).status_code == 401
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "cliente@example.test", "senha": PASSWORD},
        )
        csrf = {"X-CSRF-Token": login.json()["csrf_token"]}
        assert (await client.post(path, json={"solicitacao_id": id})).status_code == 403
        assert (
            await client.post(
                path,
                headers=csrf,
                json={"solicitacao_id": id, "cliente_id": str(uuid4())},
            )
        ).status_code == 422
        response = await client.post(path, headers=csrf, json={"solicitacao_id": id})
        assert response.status_code == 200 and response.json()["estado"] == "PUBLICADA"
        assert response.headers["cache-control"] == "no-store"
        assert "resumo" not in response.text
        assert (
            await client.post(path, headers=csrf, json={"solicitacao_id": id})
        ).json() == response.json()
        assert len(provider.calls) == 2
        assert (await client.get(path + "/" + id)).json() == response.json()
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "outro@example.test", "senha": PASSWORD},
        )
        assert (await client.get(path + "/" + id)).status_code == 404
        assert (
            await client.delete(
                path + "/" + id, headers={"X-CSRF-Token": login.json()["csrf_token"]}
            )
        ).status_code == 404

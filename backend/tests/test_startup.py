import asyncio

import httpx
import pytest
from pydantic import ValidationError

from app.main import create_app


def test_health_returns_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    app = create_app()

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert app.title == "AcademIA Teste"
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("app_name", [None, "  "])
def test_startup_rejects_missing_or_blank_app_name(
    monkeypatch: pytest.MonkeyPatch,
    app_name: str | None,
) -> None:
    if app_name is None:
        monkeypatch.delenv("ACADEMIA_APP_NAME", raising=False)
    else:
        monkeypatch.setenv("ACADEMIA_APP_NAME", app_name)

    with pytest.raises(ValidationError, match="ACADEMIA_APP_NAME"):
        create_app()

import asyncio

import httpx
import pytest
from sqlalchemy import text

from app.database.connection import check_database, create_database_engine
from app.main import create_app


@pytest.mark.integration
def test_database_error_has_safe_http_response(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    app = create_app()
    engine = create_database_engine("test")
    reached_database = False

    @app.get("/_db_probe")
    def probe() -> None:
        nonlocal reached_database
        with engine.connect() as connection:
            check_database(connection, "test")
            reached_database = True
            connection.execute(text("SELECT CAST('probe_sintetico' AS integer)"))

    async def check() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            result = await client.get("/_db_probe")
            assert reached_database
            assert result.status_code == 500
            body = result.json()
            assert body["code"] == "INTERNAL_ERROR"
            assert body["correlation_id"] == result.headers["X-Correlation-ID"]
            assert body["correlation_id"] in caplog.text
            assert "probe_sintetico" not in result.text + caplog.text
            assert (await client.get("/health")).status_code == 200

    try:
        asyncio.run(check())
    finally:
        engine.dispose()

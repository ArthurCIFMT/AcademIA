import asyncio
from collections.abc import Iterator
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.contracts.time import UtcTimestamp
from app.main import create_app


class Probe(BaseModel):
    timestamp: UtcTimestamp


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    app = create_app()

    @app.post("/_probe")
    def echo(body: Probe) -> Probe:
        return body

    @app.get("/_probe/{status}")
    def fail(status: int) -> None:
        raise HTTPException(status, detail="segredo sintético")

    yield app


async def request(
    app: FastAPI,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    content: str | None = None,
    json: dict[str, str] | None = None,
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(
            method, path, headers=headers, content=content, json=json
        )


def test_health_matches_openapi(api: FastAPI) -> None:
    doc = asyncio.run(request(api, "GET", "/openapi.json")).json()
    result = asyncio.run(request(api, "GET", "/health"))
    schemas = doc["components"]["schemas"]
    responses = doc["paths"]["/health"]["get"]["responses"]
    ref = responses["200"]["content"]["application/json"]["schema"]["$ref"]
    schema = schemas[ref.rsplit("/", 1)[1]]
    assert result.status_code == 200
    assert set(result.json()) == set(schema["required"])
    assert result.json()["status"] == schema["properties"]["status"]["const"]
    UUID(result.headers["X-Correlation-ID"])


def test_malformed_json_matches_openapi_without_echoing_input(api: FastAPI) -> None:
    doc = asyncio.run(request(api, "GET", "/openapi.json")).json()
    result = asyncio.run(
        request(
            api,
            "POST",
            "/_probe",
            headers={"Content-Type": "application/json"},
            content='{"token":"segredo sintético"',
        )
    )
    errors = doc["paths"]["/_probe"]["post"]["responses"]["400"]
    ref = errors["content"]["application/json"]["schema"]["$ref"]
    schema = doc["components"]["schemas"][ref.rsplit("/", 1)[1]]
    body = result.json()
    assert result.status_code == 400
    assert set(body) == set(schema["required"])
    assert schema["properties"]["correlation_id"]["format"] == "uuid"
    assert body["code"] == "INVALID_JSON"
    assert isinstance(body["message"], str)
    assert body["details"] == []
    assert body["correlation_id"] == result.headers["X-Correlation-ID"]
    assert "segredo sintético" not in result.text


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "UNAUTHENTICATED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (409, "CONFLICT"),
    ],
)
def test_status_has_distinct_safe_code(api: FastAPI, status: int, code: str) -> None:
    correlation_id = str(uuid4())
    result = asyncio.run(
        request(
            api,
            "GET",
            f"/_probe/{status}",
            headers={"X-Correlation-ID": correlation_id},
        )
    )
    assert result.status_code == status
    assert result.json()["code"] == code
    assert result.json()["correlation_id"] == correlation_id
    assert "segredo sintético" not in result.text


def test_unknown_route_has_error_envelope(api: FastAPI) -> None:
    result = asyncio.run(
        request(api, "GET", "/ausente", headers={"X-Correlation-ID": "invalid"})
    )
    assert result.status_code == 404
    assert result.json()["code"] == "NOT_FOUND"
    UUID(result.headers["X-Correlation-ID"])


@pytest.mark.parametrize(
    ("timestamp", "status"),
    [("2026-11-07T09:00:00-03:00", 200), ("2026-11-07T09:00:00", 422)],
)
def test_timestamp_requires_offset_and_returns_utc(
    api: FastAPI, timestamp: str, status: int
) -> None:
    result = asyncio.run(request(api, "POST", "/_probe", json={"timestamp": timestamp}))
    assert result.status_code == status
    if status == 200:
        assert result.json() == {"timestamp": "2026-11-07T12:00:00Z"}
    else:
        assert result.json()["details"] == ["body"]

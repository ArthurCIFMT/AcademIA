import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.modules.ai.adapters.factory import create_adapter, credential_name
from app.modules.ai.adapters.gemini import GeminiAdapter
from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.orchestration.settings import Config, GeminiSettings
from app.modules.ai.ports.execution import ProviderError
from tests.ai.evaluation.reporting import redact_secrets, write_json

MESSAGES = [{"role": "system", "content": "JSON"}, {"role": "user", "content": "teste"}]


@pytest.fixture
def selected(monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "reserva-gemini")
    return Config.load()


def envelope() -> dict[str, Any]:
    return {
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"role": "model", "parts": [{"text": "{}"}]},
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 20,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 2,
            "totalTokenCount": 32,
        },
    }


@pytest.mark.parametrize(
    "kind",
    [
        "ok",
        "quota",
        "key",
        "server",
        "redirect",
        "timeout",
        "network",
        "model",
        "tool",
        "thought",
        "truncated",
        "usage",
        "oversized",
        "invalid",
        "choice",
    ],
)
def test_native_contract_and_single_request(selected: Config, kind: str) -> None:
    calls = []

    def handle(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        assert (
            str(req.url)
            == selected.base_url + "/models/gemini-3.5-flash-lite:generateContent"
        )
        assert req.headers["x-goog-api-key"] == "synthetic-gemini"
        assert "Authorization" not in req.headers and not req.url.query
        payload = json.loads(req.content)
        assert "tools" not in payload and "cachedContent" not in payload
        assert payload["generationConfig"] == {
            "temperature": 0.2,
            "candidateCount": 1,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "minimal", "includeThoughts": False},
        }
        if kind == "timeout":
            raise httpx.ReadTimeout("private")
        if kind == "network":
            raise httpx.ConnectError("private")
        if kind in {"quota", "key", "server", "redirect"}:
            return httpx.Response(
                {"quota": 429, "key": 403, "server": 503, "redirect": 302}[kind],
                text="private",
            )
        if kind == "oversized":
            return httpx.Response(200, text="x" * 131073)
        if kind == "invalid":
            return httpx.Response(200, text="private")
        data = envelope()
        if kind == "choice":
            data["candidates"] = ["invalid"]
        if kind == "model":
            data["modelVersion"] = "other"
        if kind == "tool":
            data["candidates"][0]["content"]["parts"] = [
                {"functionCall": {"name": "SQL"}}
            ]
        if kind == "thought":
            data["candidates"][0]["content"]["parts"][0]["thought"] = True
        if kind == "truncated":
            data["candidates"][0]["finishReason"] = "MAX_TOKENS"
        if kind == "usage":
            data["usageMetadata"]["totalTokenCount"] = 30
        return httpx.Response(200, json=data)

    client = GeminiAdapter(
        selected,
        GeminiSettings(api_key=SecretStr("synthetic-gemini")),
        transport=httpx.MockTransport(handle),
    )
    dispatched = []
    expected = {
        "quota": "QUOTA_EXCEDIDA",
        "key": "CREDENCIAL_RECUSADA",
        "server": "PROVEDOR_INDISPONIVEL",
        "redirect": "PROVEDOR_INDISPONIVEL",
        "timeout": "TIMEOUT",
        "network": "TRANSPORTE_INDISPONIVEL",
        "truncated": "SAIDA_INTERROMPIDA",
        "oversized": "SAIDA_EXCEDIDA",
    }
    try:
        if kind == "ok":
            result = client.complete(
                MESSAGES, "CHAT", 600, 20, lambda: dispatched.append(1)
            )
            assert (
                result.content == "{}"
                and result.usage
                and result.usage.completion_tokens == 12
            )
        else:
            with pytest.raises(ProviderError) as ex:
                client.complete(MESSAGES, "CHAT", 600, 20, lambda: dispatched.append(1))
            assert ex.value.code == expected.get(
                kind, "RESPOSTA_PROVEDOR_INVALIDA"
            ) and "private" not in str(ex.value)
        assert len(calls) == len(dispatched) == 1
    finally:
        client.close()


def test_factory_separates_credentials_and_rejects_cross_provider(
    selected: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "groq-private")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert credential_name(selected) == "GEMINI_API_KEY"
    adapter = create_adapter(selected)
    try:
        assert isinstance(adapter, GeminiAdapter)
        with pytest.raises(ProviderError, match="CREDENCIAL_AUSENTE"):
            adapter.complete(
                MESSAGES, "CHAT", 600, 20, lambda: pytest.fail("despacho indevido")
            )
    finally:
        adapter.close()
    with pytest.raises(ValueError, match="incompatível"):
        GroqAdapter(selected)
    for update in [
        {"provider": "groq"},
        {"base_url": "https://example.test"},
        {"model": "gemini-latest"},
    ]:
        with pytest.raises(ValidationError):
            Config.model_validate({**selected.model_dump(), **update})
    settings = GeminiSettings(
        api_key=SecretStr("hidden"), base_url="https://example.test"
    )
    with pytest.raises(ValueError):
        settings.endpoint(selected)
    assert "hidden" not in repr(settings)


def test_sanitization_covers_both_providers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "groq-secret-synthetic")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret-synthetic")
    raw = "groq-secret-synthetic gemini-secret-synthetic"
    assert "secret" not in redact_secrets(raw)
    path = tmp_path / "report.json"
    write_json(path, {"response": raw})
    assert "secret" not in path.read_text()

import json
import time
from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr

from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.orchestration.settings import Config, GroqSettings
from app.modules.ai.ports.execution import ProviderError


def envelope(content: str = "{}") -> dict[str, object]:
    return {
        "model": Config.load().model,
        "choices": [
            {
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
            "queue_time": 0.01,
        },
    }


def adapter(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> GroqAdapter:
    return GroqAdapter(
        Config.load(),
        GroqSettings(api_key=SecretStr("test-only-not-a-key")),
        transport=httpx.MockTransport(handler),
        clock=clock,
    )


def test_http_contract_no_tools_no_retry_and_actual_usage() -> None:
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        body = json.loads(request.content)
        assert request.method == "POST"
        assert str(request.url) == Config.load().base_url + "/chat/completions"
        assert body["response_format"] == {"type": "json_object"}
        assert body["model"] == Config.load().model
        assert body["reasoning_effort"] == "low" and body["include_reasoning"] is False
        assert body["max_completion_tokens"] == 600 and body["n"] == 1
        assert not body["stream"] and "tools" not in body and "max_tokens" not in body
        return httpx.Response(200, json=envelope())

    client = adapter(handle)
    dispatches = []
    try:
        completion = client.complete(
            [{"role": "system", "content": "Responda JSON"}],
            "CHAT",
            600,
            20,
            lambda: dispatches.append(1),
        )
        assert completion.usage and completion.usage.total_tokens == 30
        assert len(calls) == len(dispatches) == 1
    finally:
        client.close()


@pytest.mark.parametrize(
    "kind,code",
    [
        ("quota", "QUOTA_EXCEDIDA"),
        ("unauthorized", "CREDENCIAL_RECUSADA"),
        ("server", "PROVEDOR_INDISPONIVEL"),
        ("timeout", "TIMEOUT"),
        ("network", "TRANSPORTE_INDISPONIVEL"),
        ("redirect", "PROVEDOR_INDISPONIVEL"),
        ("invalid", "RESPOSTA_PROVEDOR_INVALIDA"),
        ("truncated", "SAIDA_INTERROMPIDA"),
        ("model", "RESPOSTA_PROVEDOR_INVALIDA"),
        ("tool", "RESPOSTA_PROVEDOR_INVALIDA"),
        ("oversized", "SAIDA_EXCEDIDA"),
    ],
)
def test_provider_failures_one_physical_request_and_safe_error(
    kind: str, code: str
) -> None:
    calls = []
    secret = "DO-NOT-EXPOSE-RESPONSE"

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout(secret)
        if kind == "network":
            raise httpx.ConnectError(secret)
        if kind in {"quota", "unauthorized", "server", "redirect"}:
            return httpx.Response(
                {"quota": 429, "unauthorized": 401, "server": 503, "redirect": 302}[
                    kind
                ],
                text=secret,
                headers={"Location": "https://example.test"},
            )
        if kind == "invalid":
            return httpx.Response(200, text=secret)
        if kind == "oversized":
            return httpx.Response(200, text="x" * 131073)
        raw = envelope()
        if kind == "truncated":
            raw["choices"][0]["finish_reason"] = "length"  # type: ignore[index]
        if kind == "model":
            raw["model"] = "unauthorized-model"
        if kind == "tool":
            raw["choices"][0]["message"]["tool_calls"] = [{"name": "SQL"}]  # type: ignore[index]
        return httpx.Response(200, json=raw)

    client = adapter(handle)
    dispatches = []
    try:
        with pytest.raises(ProviderError) as error:
            client.complete([], "CHAT", 600, 20, lambda: dispatches.append(1))
        assert error.value.code == code and secret not in str(error.value)
        assert len(calls) == len(dispatches) == 1
    finally:
        client.close()


def test_missing_key_and_untrusted_endpoint_do_not_send() -> None:
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=envelope())

    for settings, code in [
        (GroqSettings(api_key=SecretStr("")), "CREDENCIAL_AUSENTE"),
        (
            GroqSettings(
                api_key=SecretStr("test"), base_url="https://example.test/openai/v1"
            ),
            "CONFIGURACAO_INVALIDA",
        ),
    ]:
        client = GroqAdapter(
            Config.load(), settings, transport=httpx.MockTransport(handle)
        )
        try:
            with pytest.raises(ProviderError) as error:
                client.complete(
                    [],
                    "CHAT",
                    600,
                    20,
                    lambda: calls.append(httpx.Request("GET", "https://example.test")),
                )
            assert error.value.code == code and not calls
        finally:
            client.close()
    assert "test-only" not in repr(GroqSettings(api_key=SecretStr("test-only")))


def test_timeout_detects_late_success() -> None:
    now = [0.0]

    def handle(request: httpx.Request) -> httpx.Response:
        now[0] = 21.0
        return httpx.Response(200, json=envelope())

    client = adapter(handle, clock=lambda: now[0])
    try:
        with pytest.raises(ProviderError, match="TIMEOUT"):
            client.complete([], "CHAT", 600, 20, lambda: None)
    finally:
        client.close()


def test_explicit_proxy_is_optional_validated_and_not_printed() -> None:
    assert GroqSettings(proxy_url=SecretStr("")).proxy_endpoint() is None
    secret = "http://user:synthetic-secret@127.0.0.1:9999"
    settings = GroqSettings(proxy_url=SecretStr(secret))
    assert settings.proxy_endpoint() == secret and secret not in repr(settings)
    for bad in ["file:///tmp/proxy", "http://", "http://example.test/path?x=1"]:
        with pytest.raises(ValueError, match="Proxy de saída inválido"):
            GroqSettings(proxy_url=SecretStr(bad)).proxy_endpoint()

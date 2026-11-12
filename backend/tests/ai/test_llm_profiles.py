"""Seleção explícita: quota nunca dispara troca de modelo."""

import json
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.orchestration.settings import Config, GroqSettings
from app.modules.ai.ports.execution import ProviderError
from tests.ai.evaluation.reporting import identity
from tests.ai.evaluation.resume import merge_real
from tests.ai.test_evaluation_resume import parts
from tests.ai.test_groq import envelope


def test_default_stays_primary_and_candidate_has_distinct_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ACADEMIA_LLM_PROFILE", raising=False)
    primary = Config.load()
    primary_identity = identity()
    assert primary.model == "openai/gpt-oss-120b"
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "reserva-groq20b")
    reserve = Config.load()
    assert reserve.model == "openai/gpt-oss-20b"
    assert reserve.fingerprint != primary.fingerprint
    assert identity()["configuracao_sha256"] != primary_identity["configuracao_sha256"]
    primary_data, reserve_data = primary.model_dump(), reserve.model_dump()
    primary_data.pop("model")
    reserve_data.pop("model")
    assert primary_data == reserve_data


@pytest.mark.parametrize(
    "profile", ["", "automatico", "../outro.json", "gemini", "https://example.test"]
)
def test_unknown_profile_fails_closed(
    monkeypatch: pytest.MonkeyPatch, profile: str
) -> None:
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", profile)
    with pytest.raises(ValueError, match="Perfil LLM desconhecido"):
        Config.load()


@pytest.mark.parametrize("profile", ["principal", "reserva-groq20b"])
@pytest.mark.parametrize("status", [200, 429])
def test_selected_model_is_sent_once_without_fallback(
    monkeypatch: pytest.MonkeyPatch, profile: str, status: int
) -> None:
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", profile)
    selected = Config.load()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content)["model"])
        return httpx.Response(status, json=envelope())

    client = GroqAdapter(
        selected,
        GroqSettings(api_key=SecretStr("synthetic")),
        transport=httpx.MockTransport(handler),
    )
    try:
        if status == 429:
            with pytest.raises(ProviderError, match="QUOTA_EXCEDIDA"):
                client.complete([], "CHAT", 600, 20, lambda: None)
        else:
            assert client.complete([], "CHAT", 600, 20, lambda: None).usage
        assert calls == [selected.model]
        assert Config.load().model == selected.model
    finally:
        client.close()


def test_merge_refuses_other_model_even_with_same_cases(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "principal")
    a, b = parts(tmp_path)
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "reserva-groq20b")
    candidate = identity()
    report = json.loads(b.read_text())
    report.update(candidate)
    b.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="incompatível"):
        merge_real([a, b])

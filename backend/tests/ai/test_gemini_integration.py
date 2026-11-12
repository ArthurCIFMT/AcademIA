import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.gemini import GeminiAdapter
from app.modules.ai.orchestration.settings import Config, GeminiSettings
from app.modules.ai.persistence.models import Execution
from app.modules.training.publication import published_workout
from tests.ai.test_execution import request
from tests.ai.test_generation import Scenario
from tests.ai.test_generation import scenario as scenario
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.integration
def test_gemini_native_contract_publication_and_replay(
    sessions: sessionmaker[Session], scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    people, service, provider = scenario
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "reserva-gemini")
    selected = Config.load()
    native_calls = []

    def handle(req: httpx.Request) -> httpx.Response:
        native_calls.append(req)
        assert req.headers["x-goog-api-key"] == "gemini-synthetic"
        body = json.loads(req.content)
        messages = [
            {
                "role": "system",
                "content": body["systemInstruction"]["parts"][0]["text"],
            },
            {"role": "user", "content": body["contents"][0]["parts"][0]["text"]},
        ]
        raw = provider.handle(
            httpx.Request("POST", "https://example.test", json={"messages": messages})
        ).json()
        return httpx.Response(
            200,
            json={
                "modelVersion": selected.model,
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "role": "model",
                            "parts": [
                                {"text": raw["choices"][0]["message"]["content"]}
                            ],
                        },
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 100,
                    "candidatesTokenCount": 50,
                    "totalTokenCount": 150,
                },
            },
        )

    adapter = GeminiAdapter(
        selected,
        GeminiSettings(api_key=SecretStr("gemini-synthetic")),
        transport=httpx.MockTransport(handle),
    )
    service.llm = adapter
    actor = people["cliente"]
    req = request(solicitacao_id=uuid4())
    try:
        result = service.generate(actor, actor.user_id, req)
        assert result.estado == "PUBLICADA" and result.modelo == selected.model
        assert result.configuracao_sha256 == selected.fingerprint
        assert service.generate(actor, actor.user_id, req) == result
        assert len(native_calls) == 2
        with sessions.begin() as session:
            row = session.scalar(select(Execution))
            assert row and row.modelo == selected.model
            published = published_workout(session, actor, actor.user_id)
            assert published and published.parecer.estado == "PENDENTE"
    finally:
        adapter.close()

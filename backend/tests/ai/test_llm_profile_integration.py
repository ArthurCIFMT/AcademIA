"""Perfil candidato: persistência real, sem provedor remoto nos testes de contrato."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.orchestration.settings import Config
from app.modules.ai.persistence.models import Execution
from app.modules.training.publication import published_workout
from tests.ai.test_execution import request
from tests.ai.test_generation import Scenario
from tests.ai.test_generation import scenario as scenario
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.fixture(autouse=True)
def candidate_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_LLM_PROFILE", "reserva-groq20b")


@pytest.mark.integration
def test_candidate_model_is_persisted_and_replay_has_no_extra_call(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    req = request()
    result = service.generate(actor, actor.user_id, req)
    assert result.estado == "PUBLICADA"
    assert result.modelo == "openai/gpt-oss-20b"
    assert result.configuracao_sha256 == Config.load().fingerprint
    assert service.generate(actor, actor.user_id, req) == result
    assert len(provider.calls) == 2
    with sessions.begin() as session:
        row = session.scalar(select(Execution))
        assert row and row.modelo == "openai/gpt-oss-20b"
        published = published_workout(session, actor, actor.user_id)
        assert published and published.parecer.estado == "PENDENTE"

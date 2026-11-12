from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.state import RateLimited
from app.modules.identity.service import utc_now
from app.modules.training.workout_models import WorkoutVersion
from tests.ai.test_chat_integration import (
    chat_scenario as chat_scenario,
)
from tests.ai.test_chat_integration import (
    chat_service,
)
from tests.ai.test_generation import Scenario
from tests.ai.test_triage_integration import exercise
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.integration
def test_quota_recovers_after_window_without_retry(
    sessions: sessionmaker[Session],
    chat_scenario: Scenario,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.ai.test_execution import request

    people, _, _ = chat_scenario
    chat, model = chat_service(sessions, chat_scenario)
    actor = people["cliente"]
    for _ in range(6):
        chat.ask(actor, request("DUVIDA"))
    with pytest.raises(RateLimited):
        chat.ask(actor, request("DUVIDA"))
    assert len(model.calls) == 6
    future = utc_now() + timedelta(seconds=61)
    monkeypatch.setattr("app.modules.ai.chat.quota.utc_now", lambda: future)
    assert chat.ask(actor, request("DUVIDA")).estado == "RESPOSTA_PRONTA"
    assert len(model.calls) == 7


@pytest.mark.integration
def test_sixteenth_version_cannot_be_recovered_from_chat(
    sessions: sessionmaker[Session],
    chat_scenario: Scenario,
) -> None:
    from app.modules.training.publication import published_workout
    from tests.ai.test_execution import request

    people, generator, _ = chat_scenario
    chat, _ = chat_service(sessions, chat_scenario)
    actor = people["cliente"]
    first = generator.generate(actor, actor.user_id, request())
    question = request("DUVIDA")
    assert chat.ask(actor, question).resposta
    for _ in range(15):
        assert generator.generate(actor, actor.user_id, request()).estado == "PUBLICADA"
    shown = chat.turn(actor, question.solicitacao_id)
    assert not shown.resposta and not shown.fontes and chat.history(actor, 1) == []
    with sessions.begin() as session:
        expired = published_workout(
            session, actor, actor.user_id, first.versao_publicada_id
        )
        assert expired and not expired.ficha.dias and expired.ficha.explicacao is None
        assert (
            session.scalar(
                select(func.count())
                .select_from(WorkoutVersion)
                .where(WorkoutVersion.conteudo_excluido_em.is_(None))
            )
            == 15
        )


@pytest.mark.integration
def test_manual_workout_does_not_depend_on_any_ai_service(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.ai.test_evaluation_real import manual_base, prepare_onboarding
    from tests.ai.test_triage_integration import seed

    people = seed(sessions)
    item = exercise(sessions, people["admin"])
    snapshot = prepare_onboarding(sessions, people["cliente"], False)

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("Fluxo manual não deve chamar IA/embedding/Qdrant.")

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(GenerationService, "generate", fail)
    monkeypatch.setattr("app.modules.ai.generation.get_encoder", fail)
    monkeypatch.setattr("app.modules.ai.generation.get_vector_store", fail)
    assert manual_base(sessions, people, snapshot, item)

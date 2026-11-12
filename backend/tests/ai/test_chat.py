import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.chat.service import ChatService
from app.modules.ai.generation import GenerationService
from tests.ai.execution_fakes import Model
from tests.ai.test_execution import request, setup
from tests.ai.test_triage_integration import seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.integration
def test_chat_without_onboarding_isolated_and_replay(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    _, _, sources, _ = setup()
    sources.package = sources.package.model_copy(
        update={"estado": "SEM_EVIDENCIAS", "evidencias": []}
    )
    model = Model([])
    service = ChatService(
        sessions, GenerationService(sessions, llm=model, evidence=sources)
    )
    req = request("DUVIDA")
    result = service.ask(people["cliente"], req)
    assert result.estado == "ABSTENCAO" and not model.calls
    assert service.ask(people["cliente"], req).estado == "ABSTENCAO"
    assert len(service.history(people["cliente"], 1)) == 1
    assert service.history(people["outro"], 1) == []

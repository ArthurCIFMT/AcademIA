from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.modules.ai.chat.models import Message
from app.modules.ai.chat.service import ChatService
from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.state import RateLimited
from tests.ai.execution_fakes import Model
from tests.ai.test_execution import request, setup
from tests.ai.test_triage_integration import seed


@pytest.mark.integration
def test_chat_concurrent_reservations_replay_and_shared_quota() -> None:
    engine = create_database_engine("test")
    schema = "ai05_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            sessions = create_session_factory(scoped)
            people = seed(sessions)
            _, _, sources, _ = setup()
            sources.package = sources.package.model_copy(
                update={"estado": "SEM_EVIDENCIAS", "evidencias": []}
            )
            llm = Model([])
            service = ChatService(
                sessions, GenerationService(sessions, llm=llm, evidence=sources)
            )
            barrier = Barrier(8, timeout=15)

            def compete(_: int) -> str:
                barrier.wait()
                try:
                    return service.ask(people["cliente"], request("DUVIDA")).estado
                except RateLimited:
                    return "429"

            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(compete, range(8)))
            assert outcomes.count("ABSTENCAO") == 6 and outcomes.count("429") == 2
            assert len(sources.queries) == 6 and not llm.calls
            # A cota de dúvidas também bloqueia adaptação antes do RAG.
            with pytest.raises(RateLimited):
                service.ask(
                    people["cliente"],
                    request(
                        "ADAPTACAO",
                        versao_base_id=uuid4(),
                        dia_alvo=1,
                        onboarding_confirmado_id=uuid4(),
                    ),
                )
            req = request("DUVIDA")
            barrier2 = Barrier(2, timeout=10)

            def replay(_: int) -> str:
                barrier2.wait()
                return service.ask(people["outro"], req).estado

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert set(pool.map(replay, range(2))) <= {"EM_EXECUCAO", "ABSTENCAO"}
            assert len(sources.queries) == 7
            with sessions.begin() as session:
                assert session.scalar(select(func.count()).select_from(Message)) == 7
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

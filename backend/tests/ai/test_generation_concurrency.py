import time
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
from app.modules.ai.orchestration.settings import Config
from app.modules.ai.persistence.models import Execution
from app.modules.ai.persistence.state import PostgresState, RateLimited
from app.modules.ai.schemas.execution import Consumption, RunResult
from tests.ai.test_execution import request
from tests.ai.test_triage_integration import seed


@pytest.mark.integration
def test_atomic_claim_dispatch_and_shared_rate_limit_in_independent_connections() -> (
    None
):
    engine = create_database_engine("test")
    schema = "ai03_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            sessions = create_session_factory(scoped)
            actor = seed(sessions)["cliente"]
            state = PostgresState(sessions)
            req = request()
            initial = RunResult(
                solicitacao_id=req.solicitacao_id,
                estado="EM_EXECUCAO",
                motivo="INICIADA",
                modelo=Config.load().model,
                versao_prompts="v1",
                configuracao_sha256="a" * 64,
            )
            barrier = Barrier(2, timeout=10)
            calls = []

            def compete() -> bool:
                barrier.wait()
                created, _ = state.claim(
                    actor,
                    actor.user_id,
                    req,
                    "b" * 64,
                    initial,
                    time.perf_counter() + 100,
                )
                if created:
                    state.reserve(
                        actor,
                        req.solicitacao_id,
                        Consumption(
                            etapa="TRIAGEM",
                            chamadas_fisicas=0,
                            limite_saida_tokens=400,
                            prompt_bytes=100,
                            prompt_sha256="a" * 64,
                        ),
                    )
                    state.dispatched(actor, req.solicitacao_id, "TRIAGEM")
                    calls.append(1)
                return created

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: compete(), range(2)))
            assert sum(results) == 1 and len(calls) == 1
            assert (
                state.cancel(actor, req.solicitacao_id).consumo[0].chamadas_fisicas == 1
            )
            for _ in range(6):
                question = request("DUVIDA")
                receipt = initial.model_copy(
                    update={"solicitacao_id": question.solicitacao_id}
                )
                assert state.claim(
                    actor,
                    actor.user_id,
                    question,
                    "c" * 64,
                    receipt,
                    time.perf_counter() + 100,
                )[0]
                # Replay não consome outra vaga.
                assert not state.claim(
                    actor,
                    actor.user_id,
                    question,
                    "c" * 64,
                    receipt,
                    time.perf_counter() + 100,
                )[0]
            with pytest.raises(RateLimited):
                question = request("DUVIDA")
                state.claim(
                    actor,
                    actor.user_id,
                    question,
                    "c" * 64,
                    initial.model_copy(
                        update={"solicitacao_id": question.solicitacao_id}
                    ),
                    time.perf_counter() + 100,
                )
            with sessions.begin() as session:
                assert session.scalar(select(func.count()).select_from(Execution)) == 7
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

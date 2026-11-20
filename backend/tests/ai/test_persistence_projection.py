import time
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.orchestration.settings import Config
from app.modules.ai.persistence.models import Execution, StageRecord
from app.modules.ai.persistence.state import PostgresState
from app.modules.ai.schemas.execution import Completion, Consumption, RunResult, Usage
from tests.ai.test_execution import request
from tests.ai.test_triage_integration import seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.parametrize("tokens", [None, (0, 0), (101, 37)])
def test_usage_projection_distinguishes_unknown_from_reported_zero(
    tokens: tuple[int, int] | None,
) -> None:
    stage = StageRecord(
        tipo="CHAT",
        chamadas=1,
        limite_saida_tokens=600,
        prompt_bytes=250,
        prompt_sha256="a" * 64,
        tokens_entrada=tokens[0] if tokens else None,
        tokens_saida=tokens[1] if tokens else None,
    )
    view = PostgresState._consumption(stage)
    if tokens is None:
        assert view.uso is None and view.consumo_desconhecido
    else:
        assert view.uso is not None and not view.consumo_desconhecido
        assert view.uso.total_tokens == sum(tokens)
        assert (view.uso.prompt_tokens, view.uso.completion_tokens) == tokens
    assert view.chamadas_fisicas == 1


@pytest.mark.parametrize("tokens", [(None, 30), (12, None)])
def test_partial_persisted_usage_is_rejected(
    tokens: tuple[int | None, int | None],
) -> None:
    with pytest.raises(ValueError, match="Consumo persistido incoerente"):
        PostgresState._consumption(
            StageRecord(tokens_entrada=tokens[0], tokens_saida=tokens[1])
        )


@pytest.mark.integration
@pytest.mark.parametrize("tokens", [None, (0, 0), (101, 37)])
def test_durable_dispatch_usage_and_cancel_have_one_consumption_source(
    sessions: sessionmaker[Session], tokens: tuple[int, int] | None
) -> None:
    actor = seed(sessions)["cliente"]
    req = request()
    config = Config.load()
    initial = RunResult(
        solicitacao_id=req.solicitacao_id,
        estado="EM_EXECUCAO",
        motivo="INICIADA",
        modelo=config.model,
        versao_prompts="teste",
        configuracao_sha256=config.fingerprint,
    )
    state = PostgresState(sessions)
    assert state.claim(
        actor, actor.user_id, req, "b" * 64, initial, time.perf_counter() + 100
    )[0]
    state.reserve(
        actor,
        req.solicitacao_id,
        Consumption(
            etapa="TRIAGEM",
            chamadas_fisicas=0,
            limite_saida_tokens=config.stage_limits("TRIAGEM")[0],
            prompt_bytes=250,
            prompt_sha256="a" * 64,
        ),
    )
    reserved = state.lookup(actor, actor.user_id, req)
    assert reserved and reserved.consumo[0].chamadas_fisicas == 0
    assert reserved.consumo[0].uso is None and reserved.consumo[0].consumo_desconhecido
    state.dispatched(actor, req.solicitacao_id, "TRIAGEM")
    sent = state.lookup(actor, actor.user_id, req)
    assert sent and sent.consumo[0].chamadas_fisicas == 1
    assert sent.consumo[0].uso is None and sent.consumo[0].consumo_desconhecido
    usage = (
        Usage(
            prompt_tokens=tokens[0],
            completion_tokens=tokens[1],
            total_tokens=sum(tokens),
        )
        if tokens is not None
        else None
    )
    state.usage(
        actor, req.solicitacao_id, "TRIAGEM", Completion(content="{}", usage=usage)
    )
    cancelled = state.cancel(actor, req.solicitacao_id)
    assert cancelled.estado == "CANCELADA"
    assert cancelled.consumo[0].chamadas_fisicas == 1
    assert cancelled.consumo[0].uso == usage
    assert cancelled.consumo[0].consumo_desconhecido is (tokens is None)
    recovered = PostgresState(sessions, worker=uuid4()).lookup(
        actor, actor.user_id, req
    )
    assert recovered == cancelled
    with sessions.begin() as session:
        row = session.scalar(select(Execution))
        stage = session.scalar(select(StageRecord))
        assert row is not None and "consumo" not in row.resultado
        assert stage is not None and stage.estado == "RECEBIDA"
        assert not hasattr(stage, "dados")

from datetime import timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.chat.models import Message
from app.modules.ai.chat.views import present
from app.modules.ai.ports.execution import ExecutionConflict
from app.modules.ai.schemas.execution import ChatAnswer, RunResult
from app.modules.identity.service import utc_now
from app.modules.training.publication import _expire
from app.modules.training.workout_models import WorkoutVersion
from tests.ai.test_chat_integration import chat_scenario as chat_scenario
from tests.ai.test_chat_integration import chat_service
from tests.ai.test_execution import request
from tests.ai.test_generation import Scenario
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


@pytest.mark.parametrize("retained", [True, False])
def test_prior_context_visibility_respects_retention(retained: bool) -> None:
    message = Message(
        id=uuid4(),
        conversa_id=uuid4(),
        solicitacao_id=uuid4(),
        pedido={"finalidade": "DUVIDA"},
        pergunta="Pergunta sintética",
        criada_em=utc_now(),
        versao_contexto_id=uuid4(),
        estado="RESPOSTA_PRONTA",
    )
    receipt = RunResult(
        solicitacao_id=message.solicitacao_id,
        estado="RESPOSTA_PRONTA",
        motivo="RESPOSTA_VALIDADA",
        modelo="teste",
        versao_prompts="teste",
        configuracao_sha256="a" * 64,
        resposta=ChatAnswer(
            idioma="pt-BR",
            tipo="ABSTENCAO",
            texto="Resposta sintética",
            evidencias_ids=[],
        ),
    )
    session = MagicMock(spec=Session)
    session.scalars.return_value = []
    view = present(session, message, receipt, uuid4(), retained=retained)
    assert (
        view.contexto_anterior and view.versao_contexto_id == message.versao_contexto_id
    )
    assert bool(view.resposta) is retained
    assert view.estado == ("RESPOSTA_PRONTA" if retained else "ABSTENCAO")
    assert view.pergunta == message.pergunta
    message.criada_em = utc_now() - timedelta(days=91)
    with pytest.raises(ExecutionConflict):
        present(session, message, receipt, None, retained=retained)


@pytest.mark.integration
def test_history_survives_two_publications_and_does_not_feed_old_context(
    sessions: sessionmaker[Session], chat_scenario: Scenario
) -> None:
    people, generator, _ = chat_scenario
    chat, llm = chat_service(sessions, chat_scenario)
    client = people["cliente"]
    before = request("DUVIDA", mensagem="PERGUNTA-ANTES-DA-FICHA")
    chat.ask(client, before)
    first = generator.generate(client, client.user_id, request())
    during = request("DUVIDA", mensagem="PERGUNTA-PRIMEIRA-FICHA")
    chat.ask(client, during)
    second = generator.generate(client, client.user_id, request())
    assert first.versao_publicada_id != second.versao_publicada_id
    before_reads = len(llm.calls)
    history = chat.history(client, 1)
    assert {v.solicitacao_id for v in history} == {
        before.solicitacao_id,
        during.solicitacao_id,
    }
    assert all(v.contexto_anterior and v.resposta and v.fontes for v in history)
    assert chat.history(people["outro"], 1) == []
    with pytest.raises(KeyError):
        chat.turn(people["outro"], during.solicitacao_id)
    assert len(llm.calls) == before_reads
    current = request("DUVIDA", mensagem="PERGUNTA-FICHA-ATUAL")
    chat.ask(client, current)
    assert llm.calls[-1][1]["historico"] == []
    assert not chat.turn(client, current.solicitacao_id).contexto_anterior
    next_question = request("DUVIDA", mensagem="OUTRA-PERGUNTA-ATUAL")
    chat.ask(client, next_question)
    assert [h["texto"] for h in llm.calls[-1][1]["historico"]] == [current.mensagem]
    with sessions.begin() as session:
        original = session.get(WorkoutVersion, first.versao_publicada_id)
        assert original is not None
        _expire(session, client, original, uuid4(), "LIMITE_15")
    expired = chat.turn(client, during.solicitacao_id)
    assert expired.pergunta == during.mensagem
    assert expired.resposta is None and expired.fontes == []
    assert chat.turn(client, before.solicitacao_id).resposta is not None
    assert len(chat.history(client, 1)) == 4


@pytest.mark.integration
def test_history_pagination_keeps_all_contexts_and_owner(
    sessions: sessionmaker[Session], chat_scenario: Scenario
) -> None:
    from datetime import timedelta

    from sqlalchemy import select

    from app.modules.ai.persistence.models import Execution

    people, generator, _ = chat_scenario
    chat, llm = chat_service(sessions, chat_scenario)
    client = people["cliente"]
    for n in range(23):
        if n == 10:
            generator.generate(client, client.user_id, request())
        asked = request("DUVIDA", mensagem=f"Pergunta sintética {n}")
        chat.ask(client, asked)
        # Janela sintética avança: não retirar a cota do produto para testar paginação.
        with sessions.begin() as session:
            for message in session.scalars(select(Message)):
                message.criada_em -= timedelta(minutes=2)
            for execution in session.scalars(select(Execution)):
                execution.iniciada_em -= timedelta(minutes=2)
    calls = len(llm.calls)
    page1, page2 = chat.history(client, 1), chat.history(client, 2)
    assert len(page1) == 20 and len(page2) == 3
    assert len({v.solicitacao_id for v in page1 + page2}) == 23
    assert any(v.contexto_anterior for v in page1)
    assert all(v.contexto_anterior for v in page2)
    assert chat.history(client, 3) == [] and chat.history(people["outro"], 1) == []
    assert len(llm.calls) == calls

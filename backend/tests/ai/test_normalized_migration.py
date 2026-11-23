import json
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.chat.models import Message
from app.modules.ai.persistence.models import Execution
from tests.ai.test_chat_integration import chat_scenario as chat_scenario
from tests.ai.test_chat_integration import chat_service
from tests.ai.test_execution import request
from tests.ai.test_generation import Scenario
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


def snapshot(connection: Connection) -> list[dict[str, object]]:
    return list(
        connection.scalars(
            text("SELECT to_jsonb(m) FROM academia.mensagem m ORDER BY m.id")
        )
    )


@pytest.mark.integration
def test_0016_preserves_messages_results_replay_and_reversible_sources(
    migration: tuple[Connection, Config],
    sessions: sessionmaker[Session],
    chat_scenario: Scenario,
) -> None:
    conn, config = migration
    people, generator, provider = chat_scenario
    actor = people["cliente"]
    chat, llm = chat_service(sessions, chat_scenario)
    before = request("DUVIDA", mensagem="Dúvida antes da primeira ficha")
    chat.ask(actor, before)
    workout = generator.generate(actor, actor.user_id, request())
    after = request("DUVIDA", mensagem="Dúvida sobre a ficha sintética")
    chat.ask(actor, after)
    views = chat.history(actor, 1)
    messages = snapshot(conn)
    tables = set(inspect(conn).get_table_names(schema="academia"))
    with sessions.begin() as session:
        results = {r.id: r.resultado for r in session.scalars(select(Execution))}
    calls = (len(llm.calls), len(provider.calls))
    command.downgrade(config, "0015")
    old = inspect(conn)
    assert old.has_table("conversa", schema="academia")
    assert "pergunta" in {
        c["name"] for c in old.get_columns("mensagem", schema="academia")
    }
    assert (
        conn.scalar(text("SELECT count(*) FROM academia.etapa_ia WHERE dados IS NULL"))
        == 0
    )
    assert (
        conn.scalar(text("SELECT count(*) FROM academia.triagem WHERE resumo IS NULL"))
        == 0
    )
    # Simular a projeção desatualizada permitida na versão antiga: o replay já
    # usava as etapas como fonte canônica, não este array no recibo da execução.
    conn.execute(
        text(
            "UPDATE academia.execucao_ia SET resultado = "
            "jsonb_set(resultado, '{consumo}', '[]'::jsonb)"
        )
    )
    command.upgrade(config, "head")
    assert snapshot(conn) == messages
    with sessions.begin() as session:
        assert {
            r.id: r.resultado for r in session.scalars(select(Execution))
        } == results
    assert chat.history(actor, 1) == views
    assert chat.ask(actor, after).resposta
    assert calls == (len(llm.calls), len(provider.calls))
    assert not inspect(conn).has_table("conversa", schema="academia")
    assert set(inspect(conn).get_table_names(schema="academia")) == tables
    assert len(inspect(conn).get_foreign_keys("mensagem", schema="academia")) == 2
    # A referência composta protege titularidade; a simples removida era redundante.
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.execute(
            text(
                "UPDATE academia.mensagem SET cliente_id=:other "
                "WHERE versao_contexto_id=:v"
            ),
            {"other": people["outro"].user_id, "v": workout.versao_publicada_id},
        )
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.execute(
            text("UPDATE academia.mensagem SET cliente_id=:absent"), {"absent": uuid4()}
        )
    for invalid in ({}, {"mensagem": None}, {"mensagem": " "}, {"mensagem": 3}):
        with pytest.raises(DBAPIError), conn.begin_nested():
            conn.execute(
                text("UPDATE academia.mensagem SET pedido=CAST(:p AS jsonb)"),
                {"p": json.dumps(invalid)},
            )
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.execute(
            text("UPDATE academia.etapa_ia SET tokens_entrada=1, tokens_saida=NULL")
        )
    assert len(chat.history(actor, 1)) == 2 and chat.history(people["outro"], 1) == []
    command.downgrade(config, "0015")
    command.upgrade(config, "head")
    assert snapshot(conn) == messages and chat.history(actor, 1) == views


@pytest.mark.integration
@pytest.mark.parametrize("source", ["mensagem", "triagem", "etapa"])
def test_0016_rejects_divergent_legacy_copies_without_partial_change(
    migration: tuple[Connection, Config],
    sessions: sessionmaker[Session],
    chat_scenario: Scenario,
    source: str,
) -> None:
    conn, config = migration
    people, generator, _ = chat_scenario
    actor = people["cliente"]
    generator.generate(actor, actor.user_id, request())
    chat, _ = chat_service(sessions, chat_scenario)
    chat.ask(actor, request("DUVIDA"))
    command.downgrade(config, "0015")
    changes = {
        "mensagem": "UPDATE academia.mensagem SET pergunta='Outro texto sintético'",
        "triagem": "UPDATE academia.triagem SET resumo='{}'::jsonb",
        "etapa": "UPDATE academia.etapa_ia SET dados="
        "jsonb_set(dados, '{prompt_bytes}', '1'::jsonb)",
    }
    with conn.begin_nested():
        conn.execute(text(changes[source]))
        legacy = snapshot(conn)
        with pytest.raises(DBAPIError, match="0016:"), conn.begin_nested():
            command.upgrade(config, "head")
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0015"
        assert inspect(conn).has_table("conversa", schema="academia")
        assert snapshot(conn) == legacy
    # Fixture externa desfaz os dados deliberadamente incoerentes. O teste não
    # decide qual cópia privada seria correta nem deixa migration parcial.


@pytest.mark.integration
def test_normalized_message_property_uses_the_frozen_request(
    sessions: sessionmaker[Session], chat_scenario: Scenario
) -> None:
    people, _, _ = chat_scenario
    service, _ = chat_service(sessions, chat_scenario)
    actor = people["cliente"]
    req = request("DUVIDA", mensagem="Pergunta sintética preservada")
    service.ask(actor, req)
    with sessions.begin() as session:
        row = session.scalar(select(Message))
        assert row and row.pergunta == row.pedido["mensagem"] == req.mensagem
        assert "pergunta" not in Message.__table__.columns
        assert row.cliente_id == actor.user_id

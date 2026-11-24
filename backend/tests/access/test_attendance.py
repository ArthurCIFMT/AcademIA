from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.modules.access.attendance.models import Presence
from app.modules.access.attendance.projection import PassageRecord, Visit, project
from app.modules.access.attendance.service import (
    attendance_history,
    current_occupancy,
    reconcile_client,
)
from app.modules.access.authorization.models import AccessDecision, TurnstileCommand
from app.modules.access.authorization.service import record_passage
from app.modules.access.events.models import AccessEvent
from app.modules.access.integrations.turnstile.contracts import Passage
from tests.access.test_authorization import NOW, identified, people


def test_projection_orders_events_and_keeps_one_presence_per_visit() -> None:
    ids = [UUID(int=value) for value in (1, 5, 7, 9, 3, 11, 13)]
    directions = ["SAIDA", "ENTRADA", "ENTRADA", "SAIDA", "SAIDA", "ENTRADA", "SAIDA"]
    seconds = [0, 1, 1, 1, 1, 2, 3]
    passages = [
        PassageRecord(key, direction, NOW + timedelta(seconds=offset))
        for key, direction, offset in zip(ids, directions, seconds, strict=True)
    ]
    result = project(reversed(passages))
    assert result == project(passages)
    assert result.visits == (Visit(ids[1], ids[4]), Visit(ids[5], ids[6]))
    assert result.outcomes == dict(
        zip(
            ids,
            [
                "SAIDA_SEM_ENTRADA",
                "ENTRADA_REGISTRADA",
                "ENTRADA_REPETIDA",
                "SAIDA_SEM_ENTRADA",
                "SAIDA_REGISTRADA",
                "ENTRADA_REGISTRADA",
                "SAIDA_REGISTRADA",
            ],
            strict=True,
        )
    )
    assert project(()).visits == ()


def create_passage(
    db: Session, client: UUID, at: datetime, *, entering: bool
) -> Passage:
    direction = "ENTRY" if entering else "EXIT"
    event_id = identified(db, client, NOW, direction="ENTRADA" if entering else "SAIDA")
    decision = AccessDecision(
        id=uuid4(),
        evento_id=event_id,
        resultado="ALLOW",
        motivo="TESTE",
        criada_em=NOW,
        regra_json={},
    )
    db.add(decision)
    db.flush()
    request_id = uuid4()
    db.add(
        TurnstileCommand(
            id=uuid4(),
            decisao_id=decision.id,
            request_id=request_id,
            direcao=direction,
            expira_em=NOW + timedelta(minutes=1),
            estado="ACEITO",
        )
    )
    db.flush()
    return Passage(
        schema_version=1,
        event_id=uuid4(),
        request_id=request_id,
        direction=direction,
        occurred_at=at,
        simulated=True,
    )


def saved(db: Session, passage: Passage) -> AccessEvent:
    return db.scalars(
        select(AccessEvent).where(
            AccessEvent.origem == "CATRACA_SIMULADA",
            AccessEvent.event_id_externo == str(passage.event_id),
        )
    ).one()


@pytest.mark.integration
@pytest.mark.database
def test_out_of_order_confirmation_history_and_migration_backfill(
    migration: Connection,
) -> None:
    sessions = create_session_factory(migration)
    now = NOW + timedelta(seconds=20)
    a = NOW + timedelta(seconds=3)
    b = NOW + timedelta(seconds=5)
    c = NOW + timedelta(seconds=9)
    with sessions.begin() as db:
        _, client = people(db)
        entry = create_passage(db, client, a, entering=True)
        repeated = create_passage(db, client, b, entering=True)
        exit_ = create_passage(db, client, c, entering=False)
        orphan = create_passage(db, client, c, entering=False)
        future = create_passage(db, client, now, entering=True)
        unlinked = AccessEvent(
            id=uuid4(),
            cliente_id=client,
            ocorrido_em=NOW,
            tipo="PASSAGEM_SIMULADA",
            direcao="ENTRADA",
            origem="CATRACA_SIMULADA",
            event_id_externo=str(uuid4()),
            payload_hash="b" * 64,
        )
        db.add(unlinked)

        def clock() -> datetime:
            return now

        assert record_passage(db, exit_, clock)
        assert saved(db, exit_).resultado_presenca == "SAIDA_SEM_ENTRADA"
        assert current_occupancy(db) == 0
        assert record_passage(db, repeated, clock)
        assert current_occupancy(db) == 0
        assert record_passage(db, entry, clock)
        assert record_passage(db, orphan, clock)
        assert not record_passage(db, orphan, clock)
        assert record_passage(db, future, clock)
        assert current_occupancy(db) == 1
        assert saved(db, repeated).resultado_presenca == "ENTRADA_REPETIDA"
        assert sorted(
            saved(db, row).resultado_presenca or "" for row in (exit_, orphan)
        ) == [
            "SAIDA_REGISTRADA",
            "SAIDA_SEM_ENTRADA",
        ]
        assert unlinked.resultado_presenca is None
        assert attendance_history(db, client, NOW, c).total == 1
        assert attendance_history(db, client, NOW, now).visits[0].exited_at == c
        end = now + timedelta(seconds=1)
        before = attendance_history(db, client, NOW, end, page=2, limit=1)
        assert before.total == 2
        assert before.visits[0].entered_at == a
        assert (
            attendance_history(db, client, NOW, end, limit=1).visits[0].entered_at
            == now
        )
        assert attendance_history(db, uuid4(), NOW, end).total == 0
        assert attendance_history(db, client, NOW, end, page=3, limit=1).total == 2
        raw_ids = (
            unlinked.id,
            *(saved(db, p).id for p in (entry, repeated, exit_, orphan, future)),
        )
        results = [db.get_one(AccessEvent, key).resultado_presenca for key in raw_ids]
        reconcile_client(db, client)
        assert attendance_history(db, client, NOW, end, page=2, limit=1) == before

    config = Config(str(Path(__file__).resolve().parents[3] / "database/alembic.ini"))
    config.attributes.update(connection=migration, database_target="test")
    command.downgrade(config, "0023")
    command.upgrade(config, "0024")
    with sessions.begin() as db:
        assert attendance_history(db, client, NOW, end, page=2, limit=1) == before
        assert current_occupancy(db) == 1
        assert [
            db.get_one(AccessEvent, key).resultado_presenca for key in raw_ids
        ] == results


@pytest.mark.integration
def test_concurrent_passages_from_two_commands_leave_one_open_presence() -> None:
    engine = create_database_engine("test")
    schema = "acs05_" + uuid4().hex
    with engine.begin() as connection:
        check_database(connection, "test")
        connection.execute(CreateSchema(schema))
    try:
        scoped = engine.execution_options(schema_translate_map={"academia": schema})
        with scoped.begin() as connection:
            Base.metadata.create_all(connection)
        sessions = create_session_factory(scoped)
        with sessions.begin() as db:
            _, client = people(db)
            first = create_passage(db, client, NOW, entering=True)
            second = create_passage(
                db, client, NOW + timedelta(seconds=1), entering=True
            )
        barrier = Barrier(2)

        def confirm(passage: Passage) -> bool:
            with sessions.begin() as db:
                barrier.wait(timeout=10)
                return record_passage(db, passage, lambda: NOW + timedelta(seconds=2))

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(confirm, (first, second))) == [True, True]
        with sessions.begin() as db:
            assert current_occupancy(db) == 1
            assert saved(db, first).resultado_presenca == "ENTRADA_REGISTRADA"
            assert saved(db, second).resultado_presenca == "ENTRADA_REPETIDA"
            assert len(db.scalars(select(Presence)).all()) == 1
    finally:
        try:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        finally:
            engine.dispose()

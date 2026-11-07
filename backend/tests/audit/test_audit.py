from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import Connection, inspect, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.events.contracts import AuditEvent
from app.events.models import OutboxRecord
from app.events.outbox import consume_next
from app.modules.audit.models import AuditRecord
from app.modules.audit.service import record_audit


@pytest.fixture
def event() -> AuditEvent:
    return AuditEvent(
        id=uuid4(),
        actor_id=uuid4(),
        action="perfil.atualizado",
        resource_type="perfil",
        resource_id=uuid4(),
        correlation_id=uuid4(),
        occurred_at=datetime.now(UTC),
    )


def migration_config(connection: Connection) -> Config:
    ini = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
    config = Config(str(ini))
    config.attributes["connection"] = connection
    config.attributes["database_target"] = "test"
    return config


@pytest.fixture
def migrated_connection() -> Iterator[Connection]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                command.upgrade(migration_config(connection), "0002")
                yield connection
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.mark.database
def test_audit_migration_can_return_to_baseline(
    migrated_connection: Connection,
) -> None:
    assert inspect(migrated_connection).has_table("auditoria", schema="academia")
    assert inspect(migrated_connection).has_table("outbox", schema="academia")

    command.downgrade(migration_config(migrated_connection), "0001")

    remaining = inspect(migrated_connection)
    assert remaining.has_schema("academia")
    assert not remaining.has_table("auditoria", schema="academia")
    assert not remaining.has_table("outbox", schema="academia")


def test_event_rejects_arbitrary_payload_and_versions(event: AuditEvent) -> None:
    payload = event.model_dump(mode="json")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        AuditEvent.model_validate({**payload, "anamnese": "registro sintético"})
    with pytest.raises(ValidationError, match="literal_error"):
        AuditEvent.model_validate({**payload, "schema_version": 99})


@pytest.mark.integration
def test_audit_and_outbox_follow_origin_transaction(
    migrated_connection: Connection, event: AuditEvent
) -> None:
    migrated_connection.execute(text("CREATE TEMP TABLE origin_probe (id int)"))
    sessions = create_session_factory(migrated_connection)

    with (
        pytest.raises(RuntimeError, match="falha de origem"),
        sessions.begin() as session,
    ):
        session.execute(text("INSERT INTO origin_probe VALUES (1)"))
        assert record_audit(session, event)
        raise RuntimeError("falha de origem")

    assert migrated_connection.scalar(text("SELECT count(*) FROM origin_probe")) == 0
    with sessions.begin() as session:
        assert session.get(AuditRecord, event.id) is None
        assert session.get(OutboxRecord, event.id) is None
        assert record_audit(session, event)

    with sessions.begin() as session:
        audit = session.get(AuditRecord, event.id)
        pending = session.get(OutboxRecord, event.id)
        assert audit is not None and audit.correlation_id == event.correlation_id
        assert (
            audit.ator_id == event.actor_id and audit.ocorrido_em == event.occurred_at
        )
        assert pending is not None and pending.estado == "PENDENTE"
        assert pending.payload == event.model_dump(mode="json")


@pytest.mark.integration
def test_retry_commits_one_effect_and_preserves_evidence(
    migrated_connection: Connection, event: AuditEvent
) -> None:
    migrated_connection.execute(text("CREATE TEMP TABLE delivery_probe (id uuid)"))
    sessions = create_session_factory(migrated_connection)

    def deliver(session: Session, received: AuditEvent) -> None:
        session.execute(
            text("INSERT INTO delivery_probe VALUES (:id)"), {"id": received.id}
        )

    def fail(session: Session, received: AuditEvent) -> None:
        deliver(session, received)
        raise RuntimeError("falha de entrega")

    with sessions.begin() as session:
        assert record_audit(session, event)
        assert not record_audit(session, event)
        conflicting = event.model_copy(update={"action": "perfil.inativado"})
        with pytest.raises(ValueError, match="outro conteúdo"):
            record_audit(session, conflicting)

    with (
        pytest.raises(RuntimeError, match="falha de entrega"),
        sessions.begin() as session,
    ):
        consume_next(session, fail)

    assert migrated_connection.scalar(text("SELECT count(*) FROM delivery_probe")) == 0
    with sessions.begin() as session:
        assert consume_next(session, deliver)
    with sessions.begin() as session:
        assert not consume_next(session, deliver)
        assert not record_audit(session, event)

    assert migrated_connection.scalar(text("SELECT count(*) FROM delivery_probe")) == 1
    with pytest.raises(DBAPIError, match="imutáveis"), sessions.begin() as session:
        session.execute(
            text("DELETE FROM academia.auditoria WHERE id=:id"), {"id": event.id}
        )
    with sessions.begin() as session:
        assert session.get(AuditRecord, event.id) is not None

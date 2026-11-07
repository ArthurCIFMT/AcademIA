import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from app.database.connection import create_session_factory, database_url


@pytest.mark.integration
def test_failed_write_rolls_back_entire_unit_of_work(
    test_connection: Connection,
) -> None:
    test_connection.execute(
        text("CREATE TEMP TABLE fnd05_probe (id integer PRIMARY KEY)")
    )
    sessions = create_session_factory(test_connection)

    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.execute(text("INSERT INTO fnd05_probe VALUES (1)"))
        session.execute(text("INSERT INTO fnd05_probe VALUES (1)"))

    assert test_connection.scalar(text("SELECT count(*) FROM fnd05_probe")) == 0

    with sessions.begin() as session:
        session.execute(text("INSERT INTO fnd05_probe VALUES (2)"))

    assert test_connection.scalar(text("SELECT id FROM fnd05_probe")) == 2
    assert test_connection.scalar(text("SHOW timezone")) == "UTC"


def test_test_url_refuses_development_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "ACADEMIA_TEST_DATABASE_URL", "postgresql+psycopg://test@localhost/academia_dev"
    )

    with pytest.raises(ValueError, match="academia_test"):
        database_url("test")

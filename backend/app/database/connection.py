import os
from typing import Literal

from sqlalchemy import URL, Connection, Engine, create_engine, make_url, text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker

type DatabaseTarget = Literal["dev", "test"]

_TARGETS = {
    "dev": ("ACADEMIA_DATABASE_URL", "academia_dev"),
    "test": ("ACADEMIA_TEST_DATABASE_URL", "academia_test"),
}


def database_url(target: DatabaseTarget) -> URL:
    variable, expected_db = _TARGETS[target]
    raw_url = os.environ.get(variable)
    if not raw_url:
        raise ValueError(f"Defina {variable} para acessar {expected_db}.")
    try:
        url = make_url(raw_url)
    except (ArgumentError, ValueError):
        raise ValueError(f"URL inválida em {variable}.") from None
    if url.drivername != "postgresql+psycopg" or url.database != expected_db:
        raise ValueError(
            f"{variable} deve usar postgresql+psycopg e o banco {expected_db}."
        )
    return url


def create_database_engine(target: DatabaseTarget) -> Engine:
    return create_engine(
        database_url(target),
        connect_args={"options": "-c timezone=UTC", "connect_timeout": 5},
        pool_pre_ping=True,
        hide_parameters=True,
    )


def check_database(connection: Connection, target: DatabaseTarget) -> None:
    _, expected_db = _TARGETS[target]
    actual_db = connection.scalar(text("SELECT current_database()"))
    if actual_db != expected_db:
        raise RuntimeError(f"A conexão precisa apontar para {expected_db}.")


def create_session_factory(bind: Engine | Connection) -> sessionmaker[Session]:
    return sessionmaker(
        bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

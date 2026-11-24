import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection

from app.database.connection import check_database, create_database_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def migration() -> Iterator[Connection]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                check_database(connection, "test")
                root = Path(__file__).resolve().parents[3]
                config = Config(str(root / "database/alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield connection
            finally:
                outer.rollback()
    finally:
        engine.dispose()

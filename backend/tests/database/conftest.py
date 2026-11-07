from collections.abc import Iterator

import pytest
from sqlalchemy import Connection

from app.database.connection import check_database, create_database_engine


@pytest.fixture
def test_connection() -> Iterator[Connection]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                check_database(connection, "test")
                yield connection
            finally:
                outer.rollback()
    finally:
        engine.dispose()

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect, text


@pytest.mark.database
def test_baseline_upgrade_reapply_and_downgrade(test_connection: Connection) -> None:
    config_file = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
    config = Config(str(config_file))
    config.attributes["connection"] = test_connection
    config.attributes["database_target"] = "test"

    assert not inspect(test_connection).has_schema("academia"), (
        "Use um academia_test dedicado sem migrations aplicadas."
    )
    assert not inspect(test_connection).has_table("alembic_version", schema="public")

    command.upgrade(config, "0001")
    command.upgrade(config, "0001")
    assert inspect(test_connection).has_schema("academia")
    assert test_connection.scalars(
        text("SELECT version_num FROM alembic_version")
    ).all() == ["0001"]

    command.downgrade(config, "base")
    assert not inspect(test_connection).has_schema("academia")
    assert test_connection.scalar(text("SELECT count(*) FROM alembic_version")) == 0

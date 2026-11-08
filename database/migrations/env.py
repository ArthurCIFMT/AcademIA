from importlib import import_module

from alembic import context
from sqlalchemy import Connection

from app.database.base import DATABASE_SCHEMA, Base
from app.database.connection import (
    DatabaseTarget,
    check_database,
    create_database_engine,
    database_url,
)

import_module("app.events.models")
import_module("app.modules.audit.models")
import_module("app.modules.identity.models")
import_module("app.modules.people.profiles")


def include_name(name: str | None, type_: str, _parent_names: object) -> bool:
    return type_ != "schema" or name == DATABASE_SCHEMA


def run_migrations(connection: Connection, target: DatabaseTarget) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        check_database(connection, target)
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url("dev"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = context.config.attributes.get("connection")
    target: DatabaseTarget = context.config.attributes.get("database_target", "dev")
    if connection is not None:
        run_migrations(connection, target)
    else:
        engine = create_database_engine(target)
        try:
            with engine.connect() as connection:
                run_migrations(connection, target)
        finally:
            engine.dispose()

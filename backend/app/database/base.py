from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

DATABASE_SCHEMA = "academia"


class Base(DeclarativeBase):
    metadata = MetaData(schema=DATABASE_SCHEMA)

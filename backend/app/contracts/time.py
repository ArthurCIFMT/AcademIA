from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime


def to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


UtcTimestamp = Annotated[AwareDatetime, AfterValidator(to_utc)]

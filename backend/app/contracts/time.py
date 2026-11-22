from datetime import UTC, date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import AfterValidator, AwareDatetime

_ACADEMY_ZONE = ZoneInfo("America/Sao_Paulo")


def academy_date(instant: datetime) -> date:
    return instant.astimezone(_ACADEMY_ZONE).date()


def age_at(birth: date, today: date) -> int:
    return (
        today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    )


def to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


UtcTimestamp = Annotated[AwareDatetime, AfterValidator(to_utc)]

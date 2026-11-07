from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.contracts.time import UtcTimestamp

Code = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]*$", max_length=80)]
ResourceCode = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]*$", max_length=60)
]


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    id: UUID
    schema_version: Literal[1] = 1
    actor_id: UUID | None = None
    action: Code
    resource_type: ResourceCode
    resource_id: UUID | None = None
    reason_code: Code | None = None
    correlation_id: UUID
    occurred_at: UtcTimestamp

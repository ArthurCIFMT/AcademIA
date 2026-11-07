from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: list[str]
    correlation_id: UUID

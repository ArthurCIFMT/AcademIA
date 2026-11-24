from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

CALLBACK_PATH = "/api/v1/acesso/catraca/passagens"
Direction = Literal["ENTRY", "EXIT"]
SimulatedUtc = Annotated[
    AwareDatetime, AfterValidator(lambda instant: instant.astimezone(UTC))
]


class WireMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal[1]

    @field_validator("schema_version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("A versão deve ser um inteiro.")
        return value


class Command(WireMessage):
    request_id: UUID
    access_decision_id: UUID
    direction: Direction
    decision: Literal["ALLOW", "DENY"]
    expires_at: SimulatedUtc
    client_id: UUID | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_wire_timestamp(cls, value: object) -> object:
        if isinstance(value, datetime) or isinstance(value, str) and "T" in value:
            return value
        raise ValueError("Use data e hora ISO 8601 com fuso.")


class CommandReceipt(WireMessage):
    request_id: UUID
    status: Literal["ACCEPTED"] = "ACCEPTED"


class PassageRequest(WireMessage):
    event_id: UUID


class Passage(WireMessage):
    event_id: UUID
    request_id: UUID
    occurred_at: SimulatedUtc
    direction: Direction
    simulated: Literal[True] = True


class CallbackReceipt(WireMessage):
    event_id: UUID
    status: Literal["RECORDED"]


class SimulatedPassageReceipt(WireMessage):
    event_id: UUID
    request_id: UUID
    status: Literal["RECORDED"] = "RECORDED"
    simulated: Literal[True] = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_TURNSTILE_",
        env_ignore_empty=True,
        hide_input_in_errors=True,
    )

    url: str = "http://127.0.0.1:8011"
    callback_url: str = "http://127.0.0.1:8000" + CALLBACK_PATH
    command_token: SecretStr
    callback_token: SecretStr
    store_path: Path = Path("backend/data/turnstile.sqlite3")
    callback_timeout_seconds: Annotated[float, Field(gt=0, le=10)] = 2
    fault: Literal["NONE", "TIMEOUT", "UNAVAILABLE"] = "NONE"

    @field_validator("command_token", "callback_token")
    @classmethod
    def validate_token(cls, token: SecretStr) -> SecretStr:
        value = token.get_secret_value()
        if (
            not 32 <= len(value) <= 256
            or not value.isascii()
            or not all(char.isalnum() or char in "-_" for char in value)
        ):
            raise ValueError("Use um token aleatório no formato URL-safe.")
        return token

    @model_validator(mode="after")
    def validate_settings(self) -> Self:
        if self.command_token == self.callback_token:
            raise ValueError("Use tokens diferentes para comando e retorno.")
        for value, expected in ((self.url, ""), (self.callback_url, CALLBACK_PATH)):
            parsed = urlsplit(value)
            if (
                parsed.scheme != "http"
                or parsed.hostname != "127.0.0.1"
                or parsed.port is None
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
                or parsed.path not in ((expected,) if expected else ("", "/"))
                or parsed.netloc != f"127.0.0.1:{parsed.port}"
            ):
                raise ValueError(
                    "Use a URL HTTP de loopback e a rota de retorno contratada."
                )
        return self

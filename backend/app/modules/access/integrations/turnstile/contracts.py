from datetime import datetime
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.contracts.time import UtcTimestamp

TurnstileDirection = Literal["ENTRY", "EXIT"]
DecisionResult = Literal["ALLOW", "DENY"]
DeliveryFailure = Literal["TIMEOUT", "INDISPONIVEL", "RECUSADO", "RECIBO_INVALIDO"]


class AccessSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_", env_ignore_empty=True, hide_input_in_errors=True
    )

    turnstile_url: str = "http://127.0.0.1:8011"
    turnstile_command_token: SecretStr | None = None
    turnstile_callback_token: SecretStr | None = None
    access_modalidade_ponto: Annotated[
        str, Field(min_length=1, max_length=80, pattern=r"\S")
    ] = "Musculação"
    access_command_ttl_seconds: Annotated[int, Field(ge=1, le=120)] = 30
    access_identification_max_age_seconds: Annotated[int, Field(ge=1, le=300)] = 60
    access_turnstile_timeout_seconds: Annotated[float, Field(gt=0, le=10)] = 2

    @field_validator("turnstile_command_token", "turnstile_callback_token")
    @classmethod
    def token_format(cls, token: SecretStr | None) -> SecretStr | None:
        if token is not None:
            value = token.get_secret_value()
            if (
                not 32 <= len(value) <= 256
                or not value.isascii()
                or not all(char.isalnum() or char in "-_" for char in value)
            ):
                raise ValueError(
                    "Use um token de integração aleatório no formato URL-safe."
                )
        return token

    @model_validator(mode="after")
    def valid_connection(self) -> Self:
        if (
            self.turnstile_command_token is not None
            and self.turnstile_command_token == self.turnstile_callback_token
        ):
            raise ValueError("Use tokens distintos para comando e passagem.")
        parsed = urlsplit(self.turnstile_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.port is None
            or parsed.netloc != f"127.0.0.1:{parsed.port}"
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Configure a catraca em HTTP de loopback com porta explícita."
            )
        return self


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
    direction: TurnstileDirection
    decision: DecisionResult
    expires_at: UtcTimestamp
    client_id: UUID | None = None


class CommandAck(WireMessage):
    request_id: UUID
    status: Literal["ACCEPTED"]


class Passage(WireMessage):
    event_id: UUID
    request_id: UUID
    occurred_at: UtcTimestamp
    direction: TurnstileDirection
    simulated: Literal[True]

    @field_validator("occurred_at", mode="before")
    @classmethod
    def wire_datetime(cls, value: object) -> object:
        if isinstance(value, datetime) or isinstance(value, str) and "T" in value:
            return value
        raise ValueError("Use um instante ISO 8601 com fuso.")

    @field_validator("simulated", mode="before")
    @classmethod
    def strict_simulated(cls, value: object) -> object:
        if value is not True:
            raise ValueError("O evento precisa indicar passagem simulada.")
        return value


class PassageAck(WireMessage):
    event_id: UUID
    status: Literal["RECORDED"] = "RECORDED"

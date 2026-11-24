from datetime import datetime
from typing import Annotated, Literal, Self
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
from app.modules.access.biometrics.images import PhotoUpload

Direction = Literal["ENTRADA", "SAIDA"]
Origin = Literal["ACADEMIA", "INTEGRACAO_FACIAL"]
IdentificationStatus = Literal[
    "IDENTIFICADO",
    "DESCONHECIDO",
    "PONTUACAO_BAIXA",
    "AMBIGUO",
    "CAPTURA_INVALIDA",
    "FALHA_PROVEDOR",
]
Similarity = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]


class AccessEventsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_ACCESS_",
        env_ignore_empty=True,
        hide_input_in_errors=True,
    )
    identification_token: SecretStr | None = None
    similarity_threshold: Annotated[float, Field(gt=0, le=1)] = 0.95

    @field_validator("identification_token")
    @classmethod
    def validate_token(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            secret = value.get_secret_value()
            if (
                not 32 <= len(secret) <= 256
                or not secret.isascii()
                or not all(x.isalnum() or x in "-_" for x in secret)
            ):
                raise ValueError(
                    "Use um token de integração aleatório no formato URL-safe."
                )
        return value


class CaptureRequest(PhotoUpload):
    evento_id: UUID
    direcao: Direction


class ExternalIdentification(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    schema_version: Literal[1]
    evento_id: UUID
    ocorrido_em: UtcTimestamp
    direcao: Direction
    resultado: Literal[
        "CORRESPONDENCIA",
        "DESCONHECIDO",
        "AMBIGUO",
        "CAPTURA_INVALIDA",
        "FALHA_PROVEDOR",
    ]
    subject: UUID | None = None
    similaridade: Similarity | None = None

    @field_validator("ocorrido_em", mode="before")
    @classmethod
    def check_timestamp(cls, value: object) -> object:
        if isinstance(value, datetime) or isinstance(value, str) and "T" in value:
            return value
        raise ValueError("Informe o instante em ISO 8601 com fuso horário.")

    @model_validator(mode="after")
    def validate_match(self) -> Self:
        if self.resultado == "CORRESPONDENCIA":
            if self.subject is None or self.similaridade is None:
                raise ValueError("Correspondência requer subject e similaridade.")
        elif self.subject is not None or self.similaridade is not None:
            raise ValueError(
                "Resultado sem correspondência não recebe sujeito ou pontuação."
            )
        return self


class IdentificationReceipt(BaseModel):
    schema_version: Literal[1] = 1
    id: UUID
    evento_id: UUID
    origem: Origin
    ocorrido_em: UtcTimestamp
    direcao: Direction
    resultado: IdentificationStatus
    similaridade: Similarity | None
    cliente_id: UUID | None


class StaffIdentification(IdentificationReceipt):
    cliente_nome: str | None

from datetime import timedelta
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_AUTH_", hide_input_in_errors=True, frozen=True
    )

    origin: str
    allow_local_http: bool = False
    login_max_failures: Annotated[int, Field(ge=1)] = 5
    login_window_seconds: Annotated[int, Field(ge=1)] = 900

    @model_validator(mode="after")
    def validate_origin(self) -> Self:
        url = urlsplit(self.origin)
        if (
            not url.hostname
            or url.username is not None
            or url.password is not None
            or self.origin != f"{url.scheme}://{url.netloc}"
        ):
            raise ValueError(
                "Configure a origem exata, sem caminho, credencial ou query."
            )
        # A leitura da porta também valida o intervalo e o formato.
        _ = url.port
        if url.scheme == "https":
            return self
        if (
            url.scheme == "http"
            and self.allow_local_http
            and url.hostname in {"127.0.0.1", "localhost", "::1"}
        ):
            return self
        raise ValueError(
            "Use HTTPS ou habilite HTTP apenas para desenvolvimento local."
        )

    @property
    def secure_cookie(self) -> bool:
        return self.origin.startswith("https://")

    @property
    def login_window(self) -> timedelta:
        return timedelta(seconds=self.login_window_seconds)

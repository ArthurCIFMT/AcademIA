import os
from pathlib import Path
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.contracts.structured import StrictModel, digest
from app.modules.ai.schemas.execution import Stage


class Config(StrictModel):
    versao: Literal[2]
    provider: Literal["groq", "gemini"]
    model: Literal["openai/gpt-oss-120b", "openai/gpt-oss-20b", "gemini-3.5-flash-lite"]
    reasoning_effort: Literal["low", "minimal"]
    include_reasoning: Literal[False]
    base_url: str
    response_format: Literal["json_object"]
    temperature: float
    concurrency: Literal[1]
    embedding: dict[str, object]
    retrieval: dict[str, object]
    limits: dict[str, object]
    retention: dict[str, object]
    quality: dict[str, object]

    @model_validator(mode="after")
    def provider_contract(self) -> Self:
        if self.provider == "groq":
            valid = (
                self.model in {"openai/gpt-oss-120b", "openai/gpt-oss-20b"}
                and self.base_url == "https://api.groq.com/openai/v1"
                and self.reasoning_effort == "low"
            )
        else:
            valid = (
                self.model == "gemini-3.5-flash-lite"
                and self.base_url == "https://generativelanguage.googleapis.com/v1beta"
                and self.reasoning_effort == "minimal"
            )
        if not valid:
            raise ValueError("Contrato de provedor/modelo/endpoint incompatível.")
        return self

    @classmethod
    def load(cls) -> "Config":
        profiles = {
            "principal": "configuracao-ia-v2.json",
            "reserva-groq20b": "configuracao-ia-reserva-groq20b-v2.json",
            "reserva-gemini": "configuracao-ia-reserva-gemini-v2.json",
        }
        profile = os.environ.get("ACADEMIA_LLM_PROFILE", "principal")
        if profile not in profiles:
            raise ValueError("Perfil LLM desconhecido; não há fallback automático.")
        path = (
            Path(__file__).resolve().parents[5]
            / "docs/requisitos/schemas"
            / profiles[profile]
        )
        return cls.model_validate_json(path.read_bytes())

    @property
    def fingerprint(self) -> str:
        return digest(self.model_dump(mode="json"))

    def stage_limits(self, stage: Stage) -> tuple[int, float]:
        key = {"CHAT": "chat", "TRIAGEM": "triage", "GERACAO": "generation"}[stage]
        settings = self.limits[key]
        if not isinstance(settings, dict):
            raise ValueError("Configuração da etapa inválida.")
        return int(settings["output_tokens"]), float(settings["timeout_seconds"])

    @property
    def deadline_seconds(self) -> float:
        return float(str(self.limits["execution_timeout_seconds"]))

    @property
    def prompt_bytes(self) -> int:
        return int(str(self.limits["prompt_utf8_bytes"]))


class GroqSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_LLM_", hide_input_in_errors=True, populate_by_name=True
    )
    api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="GROQ_API_KEY", repr=False
    )
    base_url: str | None = None
    proxy_url: SecretStr | None = Field(default=None, repr=False)
    max_response_bytes: Annotated[int, Field(ge=1024, le=1048576)] = 131072

    def proxy_endpoint(self) -> str | None:
        raw = self.proxy_url.get_secret_value().strip() if self.proxy_url else ""
        if not raw:
            return None
        try:
            parsed = urlsplit(raw)
            valid = (
                parsed.scheme in {"http", "https"}
                and bool(parsed.hostname)
                and parsed.path in {"", "/"}
                and not parsed.query
                and not parsed.fragment
                and (parsed.port is None or 1 <= parsed.port <= 65535)
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Proxy de saída inválido.")
        return raw

    def endpoint(self, config: Config) -> str:
        endpoint = (self.base_url or config.base_url).rstrip("/")
        expected, actual = urlsplit(config.base_url), urlsplit(endpoint)
        if (
            actual.scheme != "https"
            or actual.hostname != expected.hostname
            or actual.port != expected.port
            or actual.path != expected.path
            or actual.username
            or actual.password
            or actual.query
            or actual.fragment
        ):
            raise ValueError("Endpoint incompatível com o provedor configurado.")
        return endpoint + "/chat/completions"


class GeminiSettings(GroqSettings):
    api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="GEMINI_API_KEY", repr=False
    )

    def endpoint(self, config: Config) -> str:
        if config.provider != "gemini":
            raise ValueError("Provedor incompatível com credencial Gemini.")
        base = super().endpoint(config).removesuffix("/chat/completions")
        return base + "/models/" + config.model + ":generateContent"

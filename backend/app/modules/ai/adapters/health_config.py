"""Mapeamento técnico de cenários aprovados; não infere diagnóstico."""

import os
from dataclasses import replace
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.contracts.structured import StrictModel, digest
from app.modules.ai.adapters.context import PostgresContext
from app.modules.ai.ports.execution import Context, ProviderError
from app.modules.ai.schemas.execution import RunRequest
from app.modules.knowledge.retrieval.contracts import Annotation, Scope
from app.policies.access import Actor

Hash = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class HealthConfig(StrictModel):
    schema_version: Literal[1] = 1
    cenarios: dict[Hash, Scope] = {}
    anotacoes: Annotated[list[Annotation], Field(max_length=200)] = []


def load_health_config() -> HealthConfig:
    location = os.environ.get("ACADEMIA_RAG_HEALTH_CONFIG")
    if not location:
        return HealthConfig()
    with Path(location).open("rb") as stream:
        raw = stream.read(1048577)
    if len(raw) > 1048576:
        raise ValueError("Configuracao de suporte excedida.")
    return HealthConfig.model_validate_json(raw)


class ConfiguredContext(PostgresContext):
    def resolve(self, actor: Actor, client_id: UUID, request: RunRequest) -> Context:
        context = super().resolve(actor, client_id, request)
        if request.finalidade == "DUVIDA":
            return context
        try:
            config = load_health_config()
        except (ValueError, OSError):
            raise ProviderError("SUPORTE_SAUDE_INDISPONIVEL") from None
        summary = context.preparation.resumo if context.preparation else None
        scope = config.cenarios.get(summary.sha256) if summary else None
        return replace(
            context,
            health_scope=scope or context.health_scope,
            fingerprint=digest(
                {
                    "context": context.fingerprint,
                    "health_config": config.model_dump(mode="json"),
                }
            ),
        )

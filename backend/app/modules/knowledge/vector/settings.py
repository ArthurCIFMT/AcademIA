from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, StringConstraints, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.modules.knowledge.embeddings.settings import REVISION
from app.modules.knowledge.vector.contracts import EmbeddingSpace


class VectorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_VECTOR_", hide_input_in_errors=True, frozen=True
    )

    mode: Literal["local"] = "local"
    path: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        "data/qdrant"
    )
    collection: Annotated[
        str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{1,55}_v[1-9][0-9]*$")
    ] = "academia_rag_e5_v2"
    embedding_model: str = "intfloat/multilingual-e5-small"
    model_revision: str | None = REVISION
    dimension: Annotated[int, Field(ge=1, le=65536)] = 384
    # Modo servidor será implementado na fase de infraestrutura, sem fallback.
    url: SecretStr | None = Field(default=None, repr=False)

    @property
    def space(self) -> EmbeddingSpace:
        return EmbeddingSpace(
            model=self.embedding_model,
            revision=self.model_revision,
            dimension=self.dimension,
        )

    @property
    def directory(self) -> Path:
        return Path(self.path).resolve()

    @model_validator(mode="after")
    def persistent_local_only(self) -> Self:
        if self.path == ":memory:" or self.url is not None:
            raise ValueError("Use diretório persistente local, sem URL de servidor.")
        if self.directory == Path(self.directory.anchor):
            raise ValueError("Escolha um diretório específico para o banco vetorial.")
        self.space
        return self

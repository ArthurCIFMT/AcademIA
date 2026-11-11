from pathlib import Path
from typing import Annotated, Final, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

MODEL: Final = "intfloat/multilingual-e5-small"
REVISION: Final = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
FILES = (
    "config.json",
    "modules.json",
    "sentence_bert_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "sentencepiece.bpe.model",
    "1_Pooling/config.json",
    "model.safetensors",
)


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_EMBEDDING_", hide_input_in_errors=True, frozen=True
    )
    model: Literal["intfloat/multilingual-e5-small"] = MODEL
    revision: Literal["614241f622f53c4eeff9890bdc4f31cfecc418b3"] = REVISION
    path: Path = Path("models/multilingual-e5-small")
    batch_size: Annotated[int, Field(ge=1, le=32)] = 8
    timeout_seconds: Annotated[float, Field(gt=0, le=180)] = 60
    cpu_threads: Annotated[int, Field(ge=1, le=8)] = 2

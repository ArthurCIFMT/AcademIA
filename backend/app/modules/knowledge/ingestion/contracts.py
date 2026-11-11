import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pypdf import __version__

from app.modules.knowledge.schemas import Metadata


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ExtractionPolicy(StrictModel):
    version: Literal[1] = 1
    parser: str = "pypdf/" + __version__
    max_pages: Annotated[int, Field(ge=1, le=10000)] = 1000
    max_page_chars: Annotated[int, Field(ge=1)] = 100000
    max_total_chars: Annotated[int, Field(ge=1)] = 8000000
    max_stream_bytes: Annotated[int, Field(ge=1)] = 16777216
    timeout_seconds: Annotated[float, Field(gt=0, le=300)] = 60

    @property
    def fingerprint(self) -> str:
        return digest(self.model_dump(mode="json"))


def digest(value: object) -> str:
    data = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


class State(StrEnum):
    CONCLUIDA = "CONCLUIDA"
    OCR_NECESSARIO = "OCR_NECESSARIO"
    REVISAO_NECESSARIA = "REVISAO_NECESSARIA"
    FALHA = "FALHA"


class Reason(StrEnum):
    ARQUIVO_AUSENTE_OU_ALTERADO = "ARQUIVO_AUSENTE_OU_ALTERADO"
    TIPO_OU_TAMANHO_INVALIDO = "TIPO_OU_TAMANHO_INVALIDO"
    PDF_CORROMPIDO = "PDF_CORROMPIDO"
    PDF_PROTEGIDO = "PDF_PROTEGIDO"
    TEXTO_INVALIDO = "TEXTO_INVALIDO"
    SEM_CONTEUDO_TEXTUAL = "SEM_CONTEUDO_TEXTUAL"
    PAGINA_SEM_CAMADA_TEXTUAL = "PAGINA_SEM_CAMADA_TEXTUAL"
    CARACTERES_ILEGIVEIS = "CARACTERES_ILEGIVEIS"
    AVISOS_DO_PARSER = "AVISOS_DO_PARSER"
    LIMITE_EXCEDIDO = "LIMITE_EXCEDIDO"
    TIMEOUT = "TIMEOUT"
    ERRO_DO_PROCESSADOR = "ERRO_DO_PROCESSADOR"


class Section(StrictModel):
    titulo: str
    origem: Literal["MARCADOR_PDF", "DECLARADA", "CABECALHO_TXT"]
    linha: int | None = None


class Page(StrictModel):
    numero: int | None
    texto: str
    texto_sha256: str
    situacao: Literal["TEXTO", "EM_BRANCO", "OCR_NECESSARIO", "REVISAO_NECESSARIA"]
    secoes: list[Section] = []
    linha_inicio: int | None = None
    linha_fim: int | None = None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.texto_sha256 != hashlib.sha256(self.texto.encode()).hexdigest():
            raise ValueError("Hash textual inconsistente.")
        if self.situacao == "TEXTO" and not self.texto.strip():
            raise ValueError("Página textual vazia.")
        return self


class ParsedDocument(StrictModel):
    estado: State
    motivos: list[Reason] = []
    paginas: list[Page] = []
    avisos_parser: Annotated[int, Field(ge=0)] = 0
    avisos_estruturais: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def usable(self) -> Self:
        if self.estado == State.CONCLUIDA and (
            self.motivos
            or not any(p.texto.strip() for p in self.paginas)
            or any(p.situacao not in {"TEXTO", "EM_BRANCO"} for p in self.paginas)
        ):
            raise ValueError("Extração incompleta não é sucesso.")
        if self.estado != State.CONCLUIDA and not self.motivos:
            raise ValueError("Falha sem motivo.")
        return self


class ExtractionResult(StrictModel):
    schema_version: Literal[1] = 1
    id: UUID
    documento_versao_id: UUID
    aprovacao_revisao: Annotated[int, Field(ge=1)]
    arquivo_sha256: str
    formato: Literal["PDF", "TXT"]
    metadados: Metadata
    config_sha256: str
    politica: ExtractionPolicy
    criado_em: datetime
    tentativa: Annotated[int, Field(ge=1, le=3)] = 1
    historico: list[dict[str, str]] = []
    resultado: ParsedDocument

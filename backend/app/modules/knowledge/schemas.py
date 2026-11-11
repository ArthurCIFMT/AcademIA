from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.contracts.time import UtcTimestamp
from app.modules.onboarding.schemas import PrivateInput

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
Purpose = Literal["DUVIDAS", "GERACAO_GERAL", "TRIAGEM", "DUVIDAS_SAUDE_GERAL"]
MAX_BYTES = 25 * 1024 * 1024
MAX_BASE64 = ((MAX_BYTES + 2) // 3) * 4


class Metadata(PrivateInput):
    titulo: Text
    origem_url: HttpUrl
    licenca: Text
    idioma: Annotated[str, StringConstraints(pattern=r"^[a-z]{2}(-[A-Za-z]{2})?$")]
    autores: Annotated[list[Text], Field(max_length=100)] = []
    ano: Annotated[int, Field(strict=True, ge=1900, le=2100)] | None = None
    paginas_declaradas: Annotated[int, Field(strict=True, ge=1, le=10000)] | None = None
    secao: Text | None = None
    finalidades: Annotated[list[Purpose], Field(min_length=1, max_length=4)]
    limites: Text

    @field_validator("titulo", "licenca", "limites", "secao")
    @classmethod
    def safe_text(cls, value: str | None) -> str | None:
        if value and "\x00" in value:
            raise ValueError("Texto inválido.")
        return value

    @field_validator("autores")
    @classmethod
    def safe_authors(cls, values: list[str]) -> list[str]:
        if any("\x00" in value for value in values):
            raise ValueError("Texto inválido.")
        return values

    @field_validator("finalidades")
    @classmethod
    def unique(cls, values: list[Purpose]) -> list[Purpose]:
        if len(values) != len(set(values)):
            raise ValueError("Finalidades repetidas.")
        return sorted(values)


class RegisterDocument(PrivateInput):
    catalogo_id: Annotated[
        str,
        StringConstraints(strip_whitespace=True, pattern=r"^[A-Z0-9][A-Z0-9_-]{1,39}$"),
    ]
    ambiente: Literal["LITERATURA", "TESTE"]
    formato: Literal["PDF", "TXT"]
    metadados: Metadata
    arquivo_base64: Annotated[
        str, Field(min_length=1, max_length=MAX_BASE64, repr=False)
    ]
    conteudo_literatura_confirmado: Literal[True]


class Decision(PrivateInput):
    revisao: Annotated[int, Field(strict=True, ge=1)]
    estado: Literal["APROVADO", "REVOGADO"]
    motivo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None
    ) = None

    @model_validator(mode="after")
    def reason(self) -> Self:
        if self.motivo is not None and "\x00" in self.motivo:
            raise ValueError("Texto inválido.")
        if self.estado == "REVOGADO" and not self.motivo:
            raise ValueError("Informe o motivo da revogação.")
        return self


class VersionView(BaseModel):
    id: UUID
    documento_id: UUID
    catalogo_id: str
    ambiente: Literal["LITERATURA", "TESTE"]
    numero: int
    sha256: str
    formato: str
    tamanho_bytes: int
    metadados: Metadata
    estado: Literal["PENDENTE", "APROVADO", "REVOGADO"]
    criado_por: UUID
    criado_em: UtcTimestamp
    aprovado_por: UUID | None
    aprovado_em: UtcTimestamp | None
    revogado_por: UUID | None
    revogado_em: UtcTimestamp | None
    motivo_revogacao: str | None
    revisao: int


class Page(BaseModel):
    itens: list[VersionView]
    pagina: int
    limite: int
    total: int


class ImportResult(BaseModel):
    documentos: int
    versoes_novas: int
    aprovadas: int
    pendentes: int
    revogadas: int

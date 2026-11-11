from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.contracts.structured import StrictModel
from app.modules.ai.triage.contracts import Signals, TriageResult
from app.modules.knowledge.retrieval.contracts import Evidence

Purpose = Literal["DUVIDA", "GERACAO", "ADAPTACAO"]
Stage = Literal["TRIAGEM", "GERACAO", "CHAT"]
Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]


class HistoryMessage(StrictModel):
    papel: Literal["user", "assistant"]
    texto: Text


class RunRequest(StrictModel):
    schema_version: Literal[1] = 1
    solicitacao_id: UUID
    finalidade: Purpose
    mensagem: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=1000)
    ] = ""
    historico: Annotated[list[HistoryMessage], Field(max_length=6)] = []
    versao_base_id: UUID | None = None

    @model_validator(mode="after")
    def limits(self) -> Self:
        if self.finalidade in {"DUVIDA", "ADAPTACAO"} and not self.mensagem:
            raise ValueError("Informe a pergunta ou solicitação.")
        if sum(len(m.texto) for m in self.historico) > 3000:
            raise ValueError("Histórico excede o limite.")
        if self.finalidade == "ADAPTACAO" and self.versao_base_id is None:
            raise ValueError("Adaptação exige versão-base.")
        if self.finalidade != "ADAPTACAO" and self.versao_base_id is not None:
            raise ValueError("Versão-base não se aplica.")
        return self


class TriageAnswer(Signals):
    atualizacao_onboarding_necessaria: StrictBool


class ChatAnswer(StrictModel):
    schema_version: Literal[1] = 1
    idioma: Literal["pt-BR"]
    tipo: Literal["INFORMACAO", "ABSTENCAO"]
    texto: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
    ]
    evidencias_ids: Annotated[list[UUID], Field(max_length=5)]


class PlanItem(StrictModel):
    exercicio_id: UUID
    ordem: Annotated[int, Field(strict=True, ge=1, le=6)]
    equipamento_ids: Annotated[list[UUID], Field(max_length=20)]
    series: Annotated[int, Field(strict=True, ge=1, le=10)]
    repeticoes: Annotated[
        str, StringConstraints(pattern=r"^[1-9][0-9]{0,2}(?:-[1-9][0-9]{0,2})?$")
    ]
    carga_kg: (
        Annotated[Decimal, Field(ge=0, le=Decimal("999999.99"), decimal_places=2)]
        | None
    )
    cadencia: Annotated[str, StringConstraints(min_length=1, max_length=40)] | None
    intervalo_segundos: Annotated[int, Field(strict=True, ge=0, le=600)]
    observacoes: Annotated[str, StringConstraints(max_length=1000)]

    @field_validator("repeticoes")
    @classmethod
    def repetitions(cls, value: str) -> str:
        bounds = [int(x) for x in value.split("-")]
        if not 1 <= bounds[0] <= bounds[-1] <= 100:
            raise ValueError("Faixa de repetições inválida.")
        return value

    @field_validator("equipamento_ids")
    @classmethod
    def unique_equipment(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Equipamento duplicado.")
        return sorted(value)


class PlanDay(StrictModel):
    titulo: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
    ]
    itens: Annotated[list[PlanItem], Field(min_length=1, max_length=6)]


class PlanAnswer(StrictModel):
    schema_version: Literal[1] = 1
    idioma: Literal["pt-BR"]
    dias: Annotated[list[PlanDay], Field(min_length=1, max_length=6)]
    explicacao: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    evidencias_ids: Annotated[list[UUID], Field(min_length=1, max_length=5)]


class Usage(StrictModel):
    prompt_tokens: Annotated[int, Field(strict=True, ge=0)]
    completion_tokens: Annotated[int, Field(strict=True, ge=0)]
    total_tokens: Annotated[int, Field(strict=True, ge=0)]

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("Consumo incoerente.")
        return self


class Completion(StrictModel):
    content: str
    usage: Usage | None = None


class Consumption(StrictModel):
    etapa: Stage
    chamadas_fisicas: int
    limite_saida_tokens: int
    prompt_bytes: int
    prompt_sha256: str
    uso: Usage | None = None
    consumo_desconhecido: bool = True


class RunResult(StrictModel):
    schema_version: Literal[1] = 1
    solicitacao_id: UUID
    estado: Literal[
        "EM_EXECUCAO",
        "PUBLICADA",
        "RESPOSTA_PRONTA",
        "PRONTA_PARA_PUBLICACAO",
        "BLOQUEADA",
        "DADOS_INSUFICIENTES",
        "ABSTENCAO",
        "CONFLITO",
        "FALHA",
        "JSON_INVALIDO",
        "SCHEMA_INVALIDO",
        "TIMEOUT",
        "CANCELADA",
        "LIMITE_EXCEDIDO",
        "INTERROMPIDA",
    ]
    motivo: str
    etapas: list[str] = []
    consumo: list[Consumption] = []
    evidencias: list[Evidence] = []
    triagem: TriageResult | None = None
    resposta: ChatAnswer | None = None
    proposta: PlanAnswer | None = None
    versao_publicada_id: UUID | None = None
    modelo: str
    versao_prompts: str
    configuracao_sha256: str

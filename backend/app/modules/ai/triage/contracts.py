from typing import Annotated, Literal, Protocol
from uuid import UUID

from pydantic import Field, StrictBool

from app.contracts.structured import StrictModel
from app.modules.ai.policies.triage import Policy
from app.modules.knowledge.retrieval.contracts import Evidence
from app.modules.onboarding.schemas import OnboardingData

DomainState = Literal[
    "DADOS_INSUFICIENTES", "BLOQUEADO_POR_SEGURANCA", "ELEGIVEL_PARA_GERACAO"
]
TechnicalState = Literal["CONCLUIDA", "AGUARDANDO_ANALISE", "FALHA", "TIMEOUT"]
Reason = Literal[
    "ONBOARDING_NAO_CONCLUIDO",
    "DADOS_INVALIDOS",
    "IDADE_AUSENTE",
    "ESCOPO_ETARIO",
    "ALERTA_GRAVE_DECLARADO",
    "DADO_DESCONHECIDO",
    "CONTEXTO_EXCEDIDO",
    "ANALISE_PENDENTE",
    "ALERTA_GRAVE_TEXTO",
    "LACUNA_OU_CONTRADICAO",
    "ANALISE_CONCLUIDA",
    "FALHA_ANALISE",
    "TIMEOUT_ANALISE",
    "SAIDA_ANALISE_INVALIDA",
    "EVIDENCIA_NAO_FORNECIDA",
    "CONTEXTO_SUPERADO",
    "RECURSOS_ALTERADOS",
    "SEM_EXERCICIOS_VIAVEIS",
]


class SnapshotRef(StrictModel):
    id: UUID
    numero: Annotated[int, Field(strict=True, ge=1)]
    revisao: Annotated[int, Field(strict=True, ge=1)]


class SummaryData(StrictModel):
    idade: Annotated[int, Field(strict=True, ge=0)]
    dados: OnboardingData


class Summary(StrictModel):
    conteudo: SummaryData
    caracteres: int
    sha256: str


class Signals(StrictModel):
    schema_version: Literal[1] = 1
    alerta_grave: StrictBool
    lacuna: StrictBool
    contradicao: StrictBool = False
    evidencias_ids: Annotated[list[UUID], Field(max_length=8)] = []


class Analyst(Protocol):
    def analyze(
        self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
    ) -> Signals: ...


class TriageView(StrictModel):
    schema_version: Literal[1] = 1
    snapshot: SnapshotRef | None
    regra_versao: int
    regra_sha256: str
    estado: DomainState | None
    estado_tecnico: TechnicalState
    motivos: list[Reason]
    resumo_sha256: str | None
    evidencias_ids: list[UUID]
    exercicios_elegiveis: int
    recursos_sha256: str | None
    geracao_permitida: bool


class TriageResult(TriageView):
    resumo: Summary | None


class AnalysisUnavailable(Exception):
    pass

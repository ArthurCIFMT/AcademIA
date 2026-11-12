"""Consultas semânticas fixas; sem reescritor LLM ou resposta pré-fabricada."""

from app.modules.ai.triage.contracts import SummaryData
from app.modules.knowledge.retrieval.contracts import Evidence

VERSION = "consulta-geracao-v2"


def generation_query(summary: SummaryData, health_context: str) -> str:
    data = summary.dados
    return (
        "Treinamento de força para adultos: prescrição de séries e repetições, "
        "frequência semanal e intervalo de descanso entre séries. "
        f"Objetivo {data.objetivo_principal}; experiência {data.experiencia}; "
        f"{data.dias_semana} dias/semana; até {data.duracao_sessao_min} minutos. "
        + health_context
    )


def recovery_query(summary: SummaryData, health_context: str) -> str:
    return (
        "Intervalo de descanso entre séries e exercícios no treinamento resistido: "
        "recuperação e tempo disponível; "
        f"objetivo {summary.dados.objetivo_principal}; "
        f"experiência {summary.dados.experiencia}. " + health_context
    )


def generation_evidence(
    primary: tuple[Evidence, ...], recovery: tuple[Evidence, ...]
) -> tuple[Evidence, ...]:
    """Até cinco trechos: três de prescrição, dois de recuperação; sem duplicar."""
    selected: dict[object, Evidence] = {}
    for evidence in (*primary[:3], *recovery[:2], *primary[3:]):
        selected.setdefault(evidence.fragmento_id, evidence)
        if len(selected) == 5:
            break
    return tuple(selected.values())

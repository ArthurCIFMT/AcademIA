from uuid import UUID

from app.modules.ai.ports.execution import Context
from app.modules.ai.schemas.execution import ChatAnswer, PlanAnswer
from app.modules.knowledge.retrieval.contracts import Evidence


def citations(
    ids: list[UUID], evidence: tuple[Evidence, ...], *, required: bool
) -> bool:
    return (
        (not required or bool(ids))
        and len(set(ids)) == len(ids)
        and set(ids) <= {e.fragmento_id for e in evidence}
    )


def validate_chat(answer: ChatAnswer, evidence: tuple[Evidence, ...]) -> None:
    if not citations(
        answer.evidencias_ids, evidence, required=answer.tipo == "INFORMACAO"
    ):
        raise ValueError("CITACAO_INVALIDA")


def validate_plan(
    plan: PlanAnswer, context: Context, evidence: tuple[Evidence, ...]
) -> None:
    prep = context.preparation
    if (
        not prep
        or not prep.resumo
        or len(plan.dias) > prep.resumo.conteudo.dados.dias_semana
    ):
        raise ValueError("DIAS_INCOMPATIVEIS")
    if not citations(plan.evidencias_ids, evidence, required=True):
        raise ValueError("CITACAO_INVALIDA")
    candidates = {c.id: c for c in context.candidates}
    for day in plan.dias:
        if [item.ordem for item in day.itens] != list(range(1, len(day.itens) + 1)):
            raise ValueError("ORDEM_INVALIDA")
        for item in day.itens:
            candidate = candidates.get(item.exercicio_id)
            if candidate is None or item.exercicio_id in context.forbidden_ids:
                raise ValueError("EXERCICIO_PROIBIDO_OU_INEXISTENTE")
            if not any(
                set(item.equipamento_ids) == set(group)
                for group in candidate.combinacoes_disponiveis
            ):
                raise ValueError("RECURSO_INDISPONIVEL")
            if candidate.dispensa_equipamento and item.equipamento_ids:
                raise ValueError("RECURSO_INCOMPATIVEL")

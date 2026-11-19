from uuid import UUID

from app.modules.ai.ports.execution import Context
from app.modules.ai.schemas.execution import ChatAnswer, PlanAnswer
from app.modules.knowledge.retrieval.contracts import Evidence


class PlanValidationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


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
        raise PlanValidationError("DIAS_INCOMPATIVEIS")
    if not citations(plan.evidencias_ids, evidence, required=True):
        raise PlanValidationError("CITACAO_INVALIDA")
    candidates = {c.id: c for c in context.candidates}
    for day in plan.dias:
        if [item.ordem for item in day.itens] != list(range(1, len(day.itens) + 1)):
            raise PlanValidationError("ORDEM_INVALIDA")
        for item in day.itens:
            candidate = candidates.get(item.exercicio_id)
            if candidate is None or item.exercicio_id in context.forbidden_ids:
                raise PlanValidationError("EXERCICIO_PROIBIDO_OU_INEXISTENTE")
            if not any(
                set(item.equipamento_ids) == set(group)
                for group in candidate.combinacoes_disponiveis
            ):
                raise PlanValidationError("RECURSO_INDISPONIVEL")
            if candidate.dispensa_equipamento and item.equipamento_ids:
                raise PlanValidationError("RECURSO_INCOMPATIVEL")

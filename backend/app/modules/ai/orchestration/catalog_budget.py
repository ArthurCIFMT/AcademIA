"""Projeção limitada e diversa do catálogo; não prescreve exercícios."""

from collections import deque

from app.modules.ai.ports.execution import Context
from app.modules.training.schemas import ExerciseCandidate


def generation_candidates(
    context: Context, limit: int
) -> tuple[ExerciseCandidate, ...]:
    if not 1 <= limit <= 40:
        raise ValueError("LIMITE_CATALOGO_INVALIDO")
    available = [
        item for item in context.candidates if item.id not in context.forbidden_ids
    ]
    base_ids = (
        {item.exercicio_id for day in context.base_plan.dias for item in day.itens}
        if context.base_plan
        else set()
    )
    chosen = [item for item in available if item.id in base_ids]
    # Além da base preservada, oferecer ao menos uma alternativa viável.
    budget = min(40, max(limit, len(chosen) + 1 if chosen else 0))
    selected = {item.id for item in chosen}
    groups: dict[str, deque[ExerciseCandidate]] = {}
    for item in available:
        if item.id not in selected:
            groups.setdefault(item.grupo_muscular.casefold().strip(), deque()).append(
                item
            )
    while len(chosen) < budget and groups:
        for key in sorted(list(groups)):
            item = groups[key].popleft()
            chosen.append(item)
            if not groups[key]:
                del groups[key]
            if len(chosen) >= budget:
                break
    return tuple(chosen)


def candidate_payload(candidate: ExerciseCandidate) -> dict[str, object]:
    return candidate.model_dump(mode="json", exclude={"descricao"})

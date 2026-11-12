"""Texto publicado deriva dos campos validados, sem alegar eficácia científica."""

from app.modules.ai.schemas.execution import PlanAnswer


def present_plan(plan: PlanAnswer, *, adaptation: bool) -> PlanAnswer:
    days = [
        day if adaptation else day.model_copy(update={"titulo": f"Dia {index}"})
        for index, day in enumerate(plan.dias, 1)
    ]
    items = [item for day in days for item in day.itens]
    missing_load = sum(item.carga_kg is None for item in items)
    label = "Proposta de adaptação" if adaptation else "Proposta de treino"
    day_label = "dia" if len(days) == 1 else "dias"
    item_label = "item" if len(items) == 1 else "itens"
    text = (
        f"{label} com {len(days)} {day_label} e "
        f"{len(items)} {item_label} de exercício. "
        "As séries, repetições e pausas estão indicadas em cada item. "
    )
    if missing_load:
        load_label = "item" if missing_load == 1 else "itens"
        text += f"Carga a definir em {missing_load} {load_label}. "
    text += "As referências consultadas ficam registradas na geração."
    return plan.model_copy(update={"dias": days, "explicacao": text})

"""Dados sintéticos versionados; nunca importados como catálogo de produção."""

import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.modules.equipment.service import EquipmentCreate, create_equipment
from app.modules.training.catalog import create_exercise
from app.modules.training.schemas import ExerciseFields
from app.policies.access import Actor
from tests.ai.evaluation.reporting import ROOT


def catalog_fixture(sessions: sessionmaker[Session], actor: Actor) -> UUID:
    data = json.loads((ROOT / "docs/testes/ai06-catalogo-v1.json").read_text("utf-8"))
    resources: dict[str, UUID] = {}
    items: dict[str, UUID] = {}
    with sessions.begin() as session:
        for entry in data["equipamentos"]:
            equipment = create_equipment(
                session,
                EquipmentCreate(
                    solicitacao_id=uuid4(),
                    nome=entry["nome"],
                    ativo=entry["ativo"],
                    operacional=entry["operacional"],
                ),
                None,
            )
            resources[entry["chave"]] = equipment.id
        for entry in data["exercicios"]:
            item = create_exercise(
                session,
                ExerciseFields(
                    nome=entry["nome"],
                    descricao=entry["descricao"],
                    grupo_muscular=entry["grupo_muscular"],
                    ativo=True,
                    dispensa_equipamento=entry["dispensa_equipamento"],
                    combinacoes=(
                        [[resources[r] for r in entry["recursos"]]]
                        if entry["recursos"]
                        else []
                    ),
                ),
                actor.user_id,
                uuid4(),
            )
            items[entry["chave"]] = item.id
    return items["agachamento"]


def profile_data(
    case: dict[str, Any], dataset: dict[str, Any], triage_cases: list[dict[str, Any]]
) -> dict[str, Any]:
    if "perfil" in case:
        return dict(dataset["perfis"][case["perfil"]]["dados"])
    entry = next(
        c
        for c in triage_cases
        if c["id"] == ("T04" if case["origem"] == "triagem:T04" else "T01")
    )
    return dict(entry["entrada"]["dados"])


def within_demo_scope(case: dict[str, Any], plan: dict[str, Any] | None) -> bool:
    """Limites do pedido de demonstração, sem impor uma dose ao produto inteiro."""
    limits = case.get("limites_ficha")
    if limits is None:
        return True
    if plan is None:
        return False
    days = plan.get("dias")
    if not isinstance(days, list) or not 1 <= len(days) <= limits["max_dias"]:
        return False
    for day in days:
        if not isinstance(day, dict):
            return False
        items = day.get("itens")
        if (
            not isinstance(items, list)
            or not 1 <= len(items) <= limits["max_itens_por_dia"]
        ):
            return False
        for item in items:
            if not isinstance(item, dict):
                return False
            sets = item.get("series")
            if type(sets) is not int or not 1 <= sets <= limits["max_series"]:
                return False
    return True

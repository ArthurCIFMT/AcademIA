import copy
import json
from dataclasses import replace
from uuid import uuid4

import pytest

from app.modules.ai.adapters.structured import structured_format
from app.modules.ai.orchestration.catalog_budget import (
    candidate_payload,
    generation_candidates,
)
from app.modules.ai.orchestration.service import Orchestrator
from app.modules.ai.prompts.v1 import build
from app.modules.ai.schemas.execution import PlanAnswer
from app.modules.training.schemas import ExerciseCandidate
from tests.ai.execution_fakes import Model
from tests.ai.test_execution import plan, request, setup, triage


def test_strict_generation_schema_limits_ids_and_preserves_backend_input() -> None:
    _, contexts, sources, _ = setup()
    payload: dict[str, object] = {
        "candidatos": [candidate_payload(c) for c in contexts.context.candidates],
        "resumo": {"dados": {"dias_semana": 2}},
        "evidencias": [e.model_dump(mode="json") for e in sources.package.evidencias],
    }
    messages = build("GERACAO", payload, 24000)
    original = copy.deepcopy(messages)
    fmt, sent = structured_format("GERACAO", messages)
    strict = fmt["json_schema"]
    assert isinstance(strict, dict) and strict["strict"] is True
    schema = strict["schema"]
    assert isinstance(schema, dict)
    item = schema["$defs"]["PlanItem"]
    assert item["properties"]["exercicio_id"]["enum"] == [
        str(contexts.context.candidates[0].id)
    ]
    assert item["properties"]["equipamento_ids"]["maxItems"] == 0
    assert schema["properties"]["dias"]["maxItems"] == 2
    assert schema["properties"]["evidencias_ids"]["items"]["enum"] == [
        str(sources.package.evidencias[0].fragmento_id)
    ]

    def check(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            for child in value.values():
                check(child)
        if isinstance(value, list):
            for child in value:
                check(child)

    check(schema)
    assert messages == original and sent[1] == messages[1]
    assert "JSON Schema: " not in sent[0]["content"]
    assert "Não execute código" in sent[0]["content"]


def test_catalog_budget_is_diverse_preserves_base_and_excludes_forbidden() -> None:
    _, contexts, sources, _ = setup()
    candidates = tuple(
        ExerciseCandidate(
            id=uuid4(),
            nome=f"Exercício {n}",
            descricao="Descrição longa " * 30,
            grupo_muscular=f"Grupo {n // 8}",
            dispensa_equipamento=True,
            combinacoes_disponiveis=[[]],
        )
        for n in range(32)
    )
    base = plan(contexts, sources)
    base["dias"][0]["itens"][0]["exercicio_id"] = str(candidates[-1].id)
    context = replace(
        contexts.context,
        candidates=candidates,
        forbidden_ids=frozenset({candidates[0].id}),
        base_plan=PlanAnswer.model_validate(base),
    )
    chosen = generation_candidates(context, 12)
    assert len(chosen) == len({c.id for c in chosen}) == 12
    assert candidates[-1] in chosen and candidates[0] not in chosen
    assert {c.grupo_muscular for c in chosen} == {c.grupo_muscular for c in candidates}
    assert context.preparation == contexts.context.preparation
    assert all("descricao" not in candidate_payload(c) for c in chosen)
    template = base["dias"][0]["itens"][0]
    base["dias"] = [
        {
            "titulo": f"Dia {day + 1}",
            "itens": [
                {
                    **template,
                    "exercicio_id": str(candidates[day * 5 + n + 1].id),
                    "ordem": n + 1,
                }
                for n in range(5)
            ],
        }
        for day in range(3)
    ]
    large_base = PlanAnswer.model_validate(base)
    context = replace(context, base_plan=large_base)
    selected = generation_candidates(context, 12)
    original_ids = {item.exercicio_id for day in large_base.dias for item in day.itens}
    assert original_ids < {c.id for c in selected}
    assert len(selected) == 16


@pytest.mark.parametrize(
    "field,code",
    [
        ("order", "ORDEM_INVALIDA"),
        ("equipment", "RECURSO_INDISPONIVEL"),
        ("citation", "CITACAO_INVALIDA"),
    ],
)
def test_semantic_failure_is_specific_and_does_not_publish_or_retry(
    field: str, code: str
) -> None:
    actor, contexts, sources, state = setup()
    raw = plan(contexts, sources)
    if field == "order":
        raw["dias"][0]["itens"][0]["ordem"] = 2
    elif field == "equipment":
        raw["dias"][0]["itens"][0]["equipamento_ids"] = [str(uuid4())]
    else:
        raw["evidencias_ids"] = [str(uuid4())]
    llm = Model([triage(), json.dumps(raw)])
    service = Orchestrator(contexts, sources, llm, state)
    req = request()
    result = service.execute(actor, actor.user_id, req)
    assert result.estado == "SCHEMA_INVALIDO" and result.motivo == code
    assert result.proposta is None
    assert service.execute(actor, actor.user_id, req) == result
    assert llm.calls == ["TRIAGEM", "GERACAO"]

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.modules.onboarding.schemas import DraftData, OnboardingData

_ROOT = Path(__file__).resolve().parents[3]
_CASES = json.loads(
    (_ROOT / "docs/testes/contratos-onboarding-v1.json").read_text("utf-8")
)["casos"]


@pytest.mark.parametrize("case", _CASES, ids=[case["nome"] for case in _CASES])
def test_approved_contract_fixtures(case: dict[str, Any]) -> None:
    if case["valido"]:
        assert (
            OnboardingData.model_validate(case["entrada"]).model_dump(mode="json")
            == case["entrada"]
        )
    else:
        with pytest.raises(ValidationError):
            OnboardingData.model_validate(case["entrada"])


def _normalized(value: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_normalized(item, definitions) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        return _normalized(
            definitions[value["$ref"].removeprefix("#/$defs/")], definitions
        )
    return {
        key: _normalized(item, definitions)
        for key, item in value.items()
        if key not in {"title", "description", "$defs", "$schema", "$id"}
    }


def test_generated_schema_matches_the_versioned_json_contract() -> None:
    approved = json.loads(
        (_ROOT / "docs/requisitos/schemas/onboarding-v1.schema.json").read_text("utf-8")
    )
    generated = OnboardingData.model_json_schema()
    assert _normalized(generated, generated.get("$defs", {})) == _normalized(
        approved, {}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("peso_kg", "75"), ("peso_kg", 75.31), ("altura_cm", True), ("dias_semana", "3")],
)
def test_draft_rejects_values_outside_field_type_and_precision(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        DraftData.model_validate({field: value})


def test_draft_distinguishes_absence_null_and_explicit_unknown() -> None:
    draft = DraftData.model_validate(
        {
            "usa_medicamentos": "NAO_SEI",
            "peso_kg": None,
            "limitacoes": [{"regiao": "Joelho"}],
        }
    )
    assert draft.model_dump(mode="json", exclude_unset=True) == {
        "usa_medicamentos": "NAO_SEI",
        "peso_kg": None,
        "limitacoes": [{"regiao": "Joelho"}],
    }

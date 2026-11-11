import pytest
from pydantic import ValidationError

from app.modules.ai.followup import Source
from app.modules.training.review_schemas import RetryNotice
from tests.ai.test_execution import evidence


@pytest.mark.parametrize("attempt", [None, 1, 2])
def test_explicit_initial_or_bounded_retry(attempt: int | None) -> None:
    assert RetryNotice(tentativa_anterior=attempt).tentativa_anterior == attempt


@pytest.mark.parametrize("attempt", [0, 3, True])
def test_invalid_retry_does_not_open_extra_attempt(attempt: object) -> None:
    with pytest.raises(ValidationError):
        RetryNotice.model_validate({"tentativa_anterior": attempt})


def test_sources_expose_bibliography_not_retrieved_text_or_private_context() -> None:
    source = Source.model_validate(evidence().model_dump(mode="json"))
    assert "texto" not in source.model_dump() and "resumo" not in source.model_dump()
    assert source.fragmento_id and source.documento_versao_id


def test_portable_followup_schema_matches_api_contract() -> None:
    import json
    from pathlib import Path

    from app.modules.ai.http import FollowupView

    saved = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "docs/requisitos/schemas/acompanhamento-ia-v1.schema.json"
        ).read_text("utf-8")
    )
    assert saved == {
        "schema_version": 1,
        "acompanhamento": FollowupView.model_json_schema(),
        "reenvio": RetryNotice.model_json_schema(),
    }

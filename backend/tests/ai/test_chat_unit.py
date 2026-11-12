from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.ai.adapters.health_config import HealthConfig
from app.modules.ai.chat.http import Ask
from app.modules.ai.schemas.execution import RunRequest, request_payload


@pytest.mark.parametrize(
    "extra",
    [
        {"cliente_id": str(uuid4())},
        {"historico": []},
        {"mensagem": "x" * 1001},
        {"mensagem": ""},
        {"mensagem": "bad\u0000value"},
        {"finalidade": "ADAPTACAO"},
        {"finalidade": "GERACAO"},
    ],
)
def test_external_input_cannot_control_context(extra: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Ask.model_validate({"solicitacao_id": uuid4(), "mensagem": "Dúvida", **extra})


def test_old_request_hash_representation_remains_compatible() -> None:
    request = RunRequest(solicitacao_id=uuid4(), finalidade="GERACAO")
    assert "dia_alvo" not in request_payload(request)
    assert "onboarding_confirmado_id" not in request_payload(request)
    assert "versao_base_id" in request_payload(request)


def test_health_support_is_explicit_and_not_free_text_rule() -> None:
    assert not HealthConfig().cenarios
    with pytest.raises(ValidationError):
        HealthConfig.model_validate({"cenarios": {"paciente": "liberado"}})

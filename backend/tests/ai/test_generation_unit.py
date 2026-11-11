import pytest
from pydantic import ValidationError

from app.modules.ai.http import GenerateRequest, view
from app.modules.ai.persistence.maintenance import strip_private
from app.modules.ai.persistence.state import PostgresState
from app.modules.ai.schemas.execution import RunResult
from tests.ai.test_execution import request, setup


def test_public_request_cannot_choose_client_or_supply_plan() -> None:
    req = request()
    assert GenerateRequest(solicitacao_id=req.solicitacao_id)
    for key in ["cliente_id", "proposta", "estado", "triagem"]:
        with pytest.raises(ValidationError):
            GenerateRequest.model_validate(
                {"solicitacao_id": req.solicitacao_id, key: {}}
            )


def test_expiry_and_serialization_preserve_receipt_without_plan_copy() -> None:
    actor, contexts, _, _ = setup()
    req = request()
    result = RunResult(
        solicitacao_id=req.solicitacao_id,
        estado="DADOS_INSUFICIENTES",
        motivo="TESTE",
        modelo="modelo",
        versao_prompts="v1",
        configuracao_sha256="a" * 64,
        triagem=contexts.context.preparation,
    )
    cleaned = strip_private(result)
    assert cleaned.triagem is None and cleaned.solicitacao_id == result.solicitacao_id
    assert "proposta" not in PostgresState._serialize(result)
    public = view(result).model_dump()
    assert not {"triagem", "resumo", "proposta"} & public.keys()
    other = type(actor)(req.solicitacao_id, actor.roles)
    assert PostgresState.id(actor, req.solicitacao_id) != PostgresState.id(
        other, req.solicitacao_id
    )

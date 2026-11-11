import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.modules.ai.schemas.execution import (
    ChatAnswer,
    PlanAnswer,
    RunRequest,
    TriageAnswer,
)
from tests.ai.test_execution import chat, plan, request, setup, triage


def test_rest_json_schemas_reject_ownership_and_model_privileges() -> None:
    # Harness de contrato: não é uma rota da aplicação nem executa provider.
    app = FastAPI()
    _, contexts, sources, _ = setup()

    @app.post("/contract", response_model=PlanAnswer)
    def contract(body: RunRequest) -> PlanAnswer:
        return PlanAnswer.model_validate(plan(contexts, sources))

    with TestClient(app) as client:
        body = request().model_dump(mode="json")
        assert client.post("/contract", json=body).status_code == 200
        assert (
            client.post("/contract", json={**body, "usuario_id": "outro"}).status_code
            == 422
        )
        assert (
            client.post("/contract", json={**body, "mensagem": "x" * 1001}).status_code
            == 422
        )
        schemas = app.openapi()["components"]["schemas"]
        assert schemas["RunRequest"]["additionalProperties"] is False
        assert schemas["PlanAnswer"]["additionalProperties"] is False
    assert ChatAnswer.model_validate_json(chat(sources)).idioma == "pt-BR"
    assert TriageAnswer.model_validate_json(triage()).alerta_grave is False
    assert "parecer" not in json.dumps(PlanAnswer.model_json_schema())


def test_portable_schema_matches_models() -> None:
    from pathlib import Path

    from app.modules.ai.schemas.execution import RunResult

    saved = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "docs/requisitos/schemas/execucao-ia-v1.schema.json"
        ).read_text("utf-8")
    )
    models: dict[str, type[BaseModel]] = {
        "entrada": RunRequest,
        "triagem": TriageAnswer,
        "chat": ChatAnswer,
        "ficha": PlanAnswer,
        "resultado_interno": RunResult,
    }
    assert saved == {
        "schema_version": 1,
        **{key: model.model_json_schema() for key, model in models.items()},
    }

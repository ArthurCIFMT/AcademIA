"""Schema estrito do transporte, preservando validações de domínio no backend."""

from typing import Any

from pydantic import BaseModel

from app.modules.ai.schemas.execution import ChatAnswer, PlanAnswer, Stage, TriageAnswer
from app.modules.ai.schemas.parsing import parse_object


def _closed(value: Any) -> Any:
    if isinstance(value, list):
        return [_closed(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {
        key: _closed(item)
        for key, item in value.items()
        if key not in {"default", "title", "format"}
    }
    if result.get("type") == "object":
        result["additionalProperties"] = False
        result["required"] = list(result.get("properties", {}))
    return result


def structured_format(
    stage: Stage, messages: list[dict[str, str]]
) -> tuple[dict[str, object], list[dict[str, str]]]:
    if (
        len(messages) != 2
        or messages[0]["role"] != "system"
        or messages[1]["role"] != "user"
    ):
        raise ValueError("MENSAGENS_INVALIDAS")
    models: dict[Stage, type[BaseModel]] = {
        "CHAT": ChatAnswer,
        "TRIAGEM": TriageAnswer,
        "GERACAO": PlanAnswer,
    }
    model = models[stage]
    schema = _closed(model.model_json_schema())
    payload = parse_object(messages[1]["content"])["dados_nao_confiaveis"]
    if not isinstance(payload, dict):
        raise ValueError("PAYLOAD_INVALIDO")
    evidences = payload.get("evidencias", [])
    if isinstance(evidences, list) and evidences:
        ids = [item["fragmento_id"] for item in evidences if isinstance(item, dict)]
        schema["properties"]["evidencias_ids"]["items"]["enum"] = ids
    if stage == "GERACAO":
        candidates = payload.get("candidatos", [])
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("CATALOGO_AUSENTE")
        item_schema = schema["$defs"]["PlanItem"]["properties"]
        item_schema["exercicio_id"]["enum"] = [item["id"] for item in candidates]
        resources = sorted(
            {
                resource
                for candidate in candidates
                for group in candidate["combinacoes_disponiveis"]
                for resource in group
            }
        )
        if resources:
            item_schema["equipamento_ids"]["items"]["enum"] = resources
        else:
            item_schema["equipamento_ids"]["maxItems"] = 0
        summary = payload.get("resumo", {})
        if isinstance(summary, dict) and isinstance(summary.get("dados"), dict):
            schema["properties"]["dias"]["maxItems"] = summary["dados"]["dias_semana"]
    transport_messages = [
        {**message, "content": message["content"].split("\nJSON Schema: ", 1)[0]}
        if message["role"] == "system"
        else dict(message)
        for message in messages
    ]
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "academia_" + stage.lower(),
            "strict": True,
            "schema": schema,
        },
    }, transport_messages

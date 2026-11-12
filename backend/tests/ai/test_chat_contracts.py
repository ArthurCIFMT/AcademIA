import json
from pathlib import Path

from app.modules.ai.adapters.health_config import HealthConfig
from app.modules.ai.chat.http import Ask
from app.modules.ai.chat.views import ChatView


def test_portable_chat_and_health_contracts() -> None:
    root = Path(__file__).resolve().parents[3] / "docs/requisitos/schemas"
    assert json.loads((root / "chat-ia-v1.schema.json").read_text("utf-8")) == {
        "schema_version": 1,
        "pedido": Ask.model_json_schema(),
        "turno": ChatView.model_json_schema(),
    }
    assert (
        json.loads((root / "suporte-saude-ia-v1.schema.json").read_text("utf-8"))
        == HealthConfig.model_json_schema()
    )

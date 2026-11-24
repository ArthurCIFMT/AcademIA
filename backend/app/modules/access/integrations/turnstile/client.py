import httpx
from pydantic import ValidationError

from app.modules.access.integrations.turnstile.contracts import (
    AccessSettings,
    Command,
    CommandAck,
    DeliveryFailure,
)


def dispatch(settings: AccessSettings, command: Command) -> DeliveryFailure | None:
    token = settings.turnstile_command_token
    if token is None:
        return "INDISPONIVEL"
    try:
        with httpx.Client(
            timeout=settings.access_turnstile_timeout_seconds, trust_env=False
        ) as api:
            response = api.post(
                settings.turnstile_url.rstrip("/") + "/commands",
                json=command.model_dump(mode="json"),
                headers={"Authorization": "Bearer " + token.get_secret_value()},
            )
    except httpx.TimeoutException:
        return "TIMEOUT"
    except httpx.HTTPError:
        return "INDISPONIVEL"
    if response.status_code == 504:
        return "TIMEOUT"
    if response.status_code == 503:
        return "INDISPONIVEL"
    if response.status_code not in {200, 202}:
        return "RECUSADO"
    try:
        receipt = CommandAck.model_validate_json(response.content)
    except ValidationError:
        return "RECIBO_INVALIDO"
    return None if receipt.request_id == command.request_id else "RECIBO_INVALIDO"

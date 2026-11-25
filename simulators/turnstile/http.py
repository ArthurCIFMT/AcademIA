from collections.abc import Callable
from datetime import UTC, datetime
from secrets import compare_digest
from time import sleep
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from simulators.turnstile.contracts import (
    CallbackReceipt,
    Command,
    CommandReceipt,
    Passage,
    PassageRequest,
    Settings,
    SimulatedPassageReceipt,
)
from simulators.turnstile.store import RejectedOperation, Store


def deliver_callback(settings: Settings, passage: Passage) -> None:
    try:
        with httpx.Client(
            timeout=settings.callback_timeout_seconds, trust_env=False
        ) as api:
            response = api.post(
                settings.callback_url,
                json=passage.model_dump(mode="json"),
                headers={
                    "Authorization": "Bearer "
                    + settings.callback_token.get_secret_value()
                },
            )
    except httpx.TimeoutException:
        raise RejectedOperation(504, "CALLBACK_TIMEOUT") from None
    except httpx.HTTPError:
        raise RejectedOperation(502, "CALLBACK_UNAVAILABLE") from None
    if response.status_code == 410:
        raise RejectedOperation(410, "CALLBACK_EXPIRED")
    if response.status_code not in {200, 201}:
        raise RejectedOperation(502, "CALLBACK_REJECTED")
    try:
        receipt = CallbackReceipt.model_validate_json(response.content)
    except ValidationError:
        raise RejectedOperation(502, "CALLBACK_INVALID_RECEIPT") from None
    if receipt.event_id != passage.event_id:
        raise RejectedOperation(502, "CALLBACK_INVALID_RECEIPT")


bearer = HTTPBearer(auto_error=False, scheme_name="ComandoCatraca")
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def create_app(
    settings: Settings,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    delivery: Callable[[Passage], None] | None = None,
) -> FastAPI:
    store = Store(settings.store_path)
    store.verify()
    app = FastAPI(title="AcademIA Catraca Fictícia", version="1.0")
    command_token = settings.command_token.get_secret_value().encode()

    def authenticate(request: Request, credentials: Credentials) -> None:
        if (
            credentials is None
            or len(request.headers.getlist("authorization")) != 1
            or not compare_digest(credentials.credentials.encode(), command_token)
        ):
            raise HTTPException(
                401, detail="UNAUTHENTICATED", headers={"WWW-Authenticate": "Bearer"}
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/commands",
        status_code=202,
        dependencies=[Depends(authenticate)],
        responses={
            200: {"model": CommandReceipt},
            401: {"description": "Credencial inválida"},
            409: {"description": "Reenvio divergente"},
            410: {"description": "Comando expirado"},
            503: {"description": "Falha simulada"},
            504: {"description": "Timeout simulado"},
        },
    )
    def command(data: Command, response: Response) -> CommandReceipt:
        if settings.fault == "UNAVAILABLE":
            raise HTTPException(503, detail="SIMULATED_UNAVAILABLE")
        if settings.fault == "TIMEOUT":
            sleep(0.5)
            raise HTTPException(504, detail="SIMULATED_TIMEOUT")
        try:
            created = store.accept(data, clock())
        except RejectedOperation as error:
            raise HTTPException(error.status, detail=error.code) from None
        response.status_code = 202 if created else 200
        return CommandReceipt(schema_version=1, request_id=data.request_id)

    @app.post(
        "/commands/{request_id}/passages",
        status_code=201,
        dependencies=[Depends(authenticate)],
        responses={
            200: {"model": SimulatedPassageReceipt},
            401: {"description": "Credencial inválida"},
            404: {"description": "Comando não encontrado"},
            409: {"description": "Negação ou passagem conflitante"},
            410: {"description": "Comando expirado ou primeira passagem fora do prazo"},
            502: {"description": "Retorno indisponível, recusado ou inválido"},
            504: {"description": "Timeout no retorno"},
        },
    )
    def passage(
        request_id: UUID, data: PassageRequest, response: Response
    ) -> SimulatedPassageReceipt:
        created = False
        try:
            event, confirmed = store.reserve_passage(request_id, data.event_id, clock())
            if not confirmed:
                if delivery is None:
                    deliver_callback(settings, event)
                else:
                    delivery(event)
                created = store.confirm(event.event_id)
        except RejectedOperation as error:
            raise HTTPException(error.status, detail=error.code) from None
        response.status_code = 201 if created else 200
        return SimulatedPassageReceipt(
            schema_version=1,
            event_id=event.event_id,
            request_id=event.request_id,
        )

    return app

import logging
from collections.abc import Mapping
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.contracts.errors import ErrorResponse

CORRELATION_HEADER = "X-Correlation-ID"
ERRORS = {
    400: ("INVALID_JSON", "O corpo da requisição deve ser um JSON válido."),
    401: ("UNAUTHENTICATED", "Autenticação necessária."),
    403: ("FORBIDDEN", "Acesso não permitido."),
    404: ("NOT_FOUND", "Recurso não encontrado."),
    409: ("CONFLICT", "A operação conflita com o estado do recurso."),
    422: ("VALIDATION_ERROR", "Verifique os dados enviados."),
    500: ("INTERNAL_ERROR", "Não foi possível concluir a operação."),
}
VALIDATION_SOURCES = {"body", "query", "path", "header", "cookie"}
SAFE_HEADERS = {"allow", "retry-after", "www-authenticate"}
logger = logging.getLogger(__name__)


def error_schemas() -> dict[int | str, dict[str, object]]:
    return {
        status: {"model": ErrorResponse, "description": message}
        for status, (_, message) in ERRORS.items()
    }


def error_response(
    request: Request,
    status: int,
    *,
    details: list[str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    code, message = ERRORS.get(status, ("HTTP_ERROR", "A requisição foi recusada."))
    correlation_id: UUID = request.state.correlation_id
    content = ErrorResponse(
        code=code, message=message, details=details or [], correlation_id=correlation_id
    )
    return JSONResponse(
        status_code=status, content=content.model_dump(mode="json"), headers=headers
    )


async def handle_http_error(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, HTTPException)
    headers = {
        name: value
        for name, value in (exc.headers or {}).items()
        if name.lower() in SAFE_HEADERS
    }
    return error_response(request, exc.status_code, headers=headers)


async def handle_validation_error(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RequestValidationError)
    errors = exc.errors()
    if any(error["type"] == "json_invalid" for error in errors):
        return error_response(request, 400)
    sources = {error["loc"][0] for error in errors if error["loc"]}
    return error_response(request, 422, details=sorted(sources & VALIDATION_SOURCES))


async def correlate(request: Request, call_next: RequestResponseEndpoint) -> Response:
    supplied = request.headers.getlist(CORRELATION_HEADER)
    correlation_id = uuid4()
    if len(supplied) == 1 and len(supplied[0]) == 36:
        try:
            correlation_id = UUID(supplied[0])
        except ValueError:
            pass

    request.state.correlation_id = correlation_id
    try:
        response = await call_next(request)
    except Exception:
        logger.error("Falha interna na API. correlation_id=%s", correlation_id)
        response = error_response(request, 500)
    response.headers[CORRELATION_HEADER] = str(correlation_id)
    return response


def install_http_contract(app: FastAPI) -> None:
    app.middleware("http")(correlate)
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)

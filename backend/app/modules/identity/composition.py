from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from threading import Lock
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import create_database_engine, create_session_factory
from app.modules.identity.accounts import validate_email
from app.modules.identity.first_access import InvalidFirstAccess, complete_first_access
from app.modules.identity.http import BrowserAuth, EmailInput
from app.modules.identity.limiter import LoginLimiter, RecoveryLimiter
from app.modules.identity.passwords import Passwords
from app.modules.identity.recovery import (
    InvalidRecovery,
    complete_recovery,
    send_recovery,
)
from app.modules.identity.repository import PostgresIdentity
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import AuthService, utc_now
from app.modules.identity.settings import AuthSettings


class PasswordTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    token: Annotated[SecretStr, Field(min_length=43, max_length=43)]
    senha: Annotated[SecretStr, Field(min_length=10, max_length=128)]


class FirstAccessRequest(PasswordTokenRequest):
    pass


class RecoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    email: EmailInput


@dataclass(frozen=True)
class IdentityRuntime:
    settings: AuthSettings
    sessions: sessionmaker[Session]
    passwords: Passwords
    limiter: LoginLimiter


def install_identity(
    app: FastAPI,
    *,
    settings: AuthSettings | None = None,
    sessions: sessionmaker[Session] | None = None,
) -> Callable[[], sessionmaker[Session]]:
    runtime: IdentityRuntime | None = None
    lock = Lock()
    recovery_limiter = RecoveryLimiter()

    def get_runtime() -> IdentityRuntime:
        nonlocal runtime
        with lock:
            if runtime is None:
                policy = settings if settings is not None else AuthSettings()
                factory = sessions
                if factory is None:
                    factory = create_session_factory(create_database_engine("dev"))
                runtime = IdentityRuntime(
                    policy,
                    factory,
                    Passwords(),
                    LoginLimiter(
                        max_failures=policy.login_max_failures,
                        window=policy.login_window,
                    ),
                )
            return runtime

    @contextmanager
    def scope() -> Iterator[AuthService]:
        current = get_runtime()
        with current.sessions.begin() as session:
            storage = PostgresIdentity(session)
            yield AuthService(
                storage,
                storage,
                current.passwords,
                current.limiter,
                role_reader=partial(effective_roles, session),
            )

    browser = BrowserAuth(scope, lambda: get_runtime().settings)
    app.state.browser_auth = browser
    app.include_router(browser.router())

    router = APIRouter(prefix="/api/v1/auth", tags=["Identidade"])

    @router.post("/first-access", status_code=204, response_class=Response)
    def activate(data: FirstAccessRequest, request: Request) -> Response:
        browser.require_origin(request)
        current = get_runtime()
        try:
            with current.sessions.begin() as session:
                complete_first_access(
                    session,
                    data.token.get_secret_value(),
                    data.senha.get_secret_value(),
                    current.passwords,
                    now=utc_now(),
                )
        except InvalidFirstAccess:
            raise HTTPException(401) from None
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @router.post("/recovery", status_code=202, response_class=Response)
    def request_recovery(
        data: RecoveryRequest, request: Request, background: BackgroundTasks
    ) -> Response:
        browser.require_origin(request)
        current = get_runtime()
        response = Response(status_code=202, headers={"Cache-Control": "no-store"})
        try:
            email = validate_email(data.email)
        except ValueError:
            return response
        ip = request.client.host if request.client else ""
        if recovery_limiter.allow(email, ip, utc_now()):
            background.add_task(
                send_recovery,
                current.sessions,
                email,
                current.settings.origin,
                request.state.correlation_id,
            )
        return response

    @router.post("/recovery/confirm", status_code=204, response_class=Response)
    def confirm_recovery(data: PasswordTokenRequest, request: Request) -> Response:
        browser.require_origin(request)
        current = get_runtime()
        try:
            with current.sessions.begin() as session:
                complete_recovery(
                    session,
                    data.token.get_secret_value(),
                    data.senha.get_secret_value(),
                    current.passwords,
                    now=utc_now(),
                )
        except InvalidRecovery:
            raise HTTPException(401) from None
        response = Response(status_code=204, headers={"Cache-Control": "no-store"})
        browser.clear_session_cookies(response)
        return response

    app.include_router(router)
    return lambda: get_runtime().sessions

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import create_database_engine, create_session_factory
from app.modules.identity.first_access import InvalidFirstAccess, complete_first_access
from app.modules.identity.http import BrowserAuth
from app.modules.identity.limiter import LoginLimiter
from app.modules.identity.passwords import Passwords
from app.modules.identity.repository import PostgresIdentity
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import AuthService, utc_now
from app.modules.identity.settings import AuthSettings


class FirstAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    token: Annotated[SecretStr, Field(min_length=43, max_length=43)]
    senha: Annotated[SecretStr, Field(min_length=10, max_length=128)]


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

    app.include_router(router)
    return lambda: get_runtime().sessions

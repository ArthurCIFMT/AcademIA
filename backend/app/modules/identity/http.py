from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints

from app.contracts.errors import ErrorResponse
from app.contracts.time import UtcTimestamp
from app.modules.identity.limiter import TooManyAttempts
from app.modules.identity.models import Role
from app.modules.identity.ports import SessionRecord
from app.modules.identity.service import (
    ABSOLUTE_AGE,
    AuthService,
    Forbidden,
    Unauthenticated,
    csrf_matches,
)
from app.modules.identity.settings import AuthSettings
from app.policies.access import Actor

SESSION_COOKIE = "academia_session"
CSRF_COOKIE = "academia_csrf"
COOKIE_PATH = "/api/v1"
CSRF_HEADER = "X-CSRF-Token"
type AuthScope = Callable[[], AbstractContextManager[AuthService]]
type EmailInput = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)
]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    email: EmailInput
    senha: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class SessionResponse(BaseModel):
    user_id: UUID
    expires_at: UtcTimestamp
    csrf_token: str
    roles: list[Role]


class BrowserAuth:
    def __init__(
        self, scope: AuthScope, settings: AuthSettings | Callable[[], AuthSettings]
    ) -> None:
        self.scope = scope
        self._settings = settings

    @property
    def settings(self) -> AuthSettings:
        return self._settings() if callable(self._settings) else self._settings

    def require_origin(self, request: Request) -> None:
        if request.headers.getlist("origin") != [self.settings.origin]:
            raise HTTPException(403)

    @contextmanager
    def request_scope(self) -> Iterator[AuthService]:
        try:
            with self.scope() as auth:
                yield auth
        except Unauthenticated:
            raise HTTPException(401) from None
        except Forbidden:
            raise HTTPException(403) from None
        except TooManyAttempts:
            raise HTTPException(429) from None

    def session_for(self, request: Request, auth: AuthService) -> SessionRecord:
        token = request.cookies.get(SESSION_COOKIE)
        if token is None:
            raise Unauthenticated
        mutating = request.method not in {"GET", "HEAD", "OPTIONS"}
        if mutating:
            self.require_origin(request)
        headers = request.headers.getlist(CSRF_HEADER)
        return auth.resolve(
            token,
            csrf=headers[0] if len(headers) == 1 else None,
            require_csrf=mutating,
        )

    def require_identity(self, request: Request) -> UUID:
        with self.request_scope() as auth:
            return self.session_for(request, auth).user_id

    def require_actor(self, request: Request) -> Actor:
        with self.request_scope() as auth:
            user_id = self.session_for(request, auth).user_id
            return Actor(user_id, auth.roles_for(user_id))

    def clear_session_cookies(self, response: Response) -> None:
        for key in (SESSION_COOKIE, CSRF_COOKIE):
            response.delete_cookie(
                key,
                path=COOKIE_PATH,
                httponly=True,
                samesite="lax",
                secure=self.settings.secure_cookie,
            )

    def router(self) -> APIRouter:
        router = APIRouter(prefix="/api/v1/auth", tags=["Identidade"])

        @router.post(
            "/login",
            responses={
                429: {"model": ErrorResponse, "description": "Limite de tentativas"}
            },
        )
        def login(
            data: LoginRequest, request: Request, response: Response
        ) -> SessionResponse:
            self.require_origin(request)
            ip = request.client.host if request.client else ""
            with self.request_scope() as auth:
                issued = auth.login(data.email, data.senha.get_secret_value(), ip)
                roles = sorted(auth.roles_for(issued.record.user_id))

            for key, value in (
                (SESSION_COOKIE, issued.token),
                (CSRF_COOKIE, issued.csrf),
            ):
                response.set_cookie(
                    key,
                    value,
                    max_age=int(ABSOLUTE_AGE.total_seconds()),
                    path=COOKIE_PATH,
                    httponly=True,
                    samesite="lax",
                    secure=self.settings.secure_cookie,
                )
            response.headers["Cache-Control"] = "no-store"
            return SessionResponse(
                user_id=issued.record.user_id,
                expires_at=issued.record.expires_at,
                csrf_token=issued.csrf,
                roles=roles,
            )

        @router.get("/session")
        def current_session(request: Request, response: Response) -> SessionResponse:
            with self.request_scope() as auth:
                session = self.session_for(request, auth)
                csrf = request.cookies.get(CSRF_COOKIE)
                if csrf is None or not csrf_matches(session, csrf):
                    raise HTTPException(403)
                roles = sorted(auth.roles_for(session.user_id))
            response.headers["Cache-Control"] = "no-store"
            return SessionResponse(
                user_id=session.user_id,
                expires_at=session.expires_at,
                csrf_token=csrf,
                roles=roles,
            )

        @router.post("/logout", status_code=204, response_class=Response)
        def logout(request: Request) -> Response:
            with self.request_scope() as auth:
                auth.logout(self.session_for(request, auth))
            response = Response(status_code=204, headers={"Cache-Control": "no-store"})
            self.clear_session_cookies(response)
            return response

        return router

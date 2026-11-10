from collections.abc import Callable, Iterator
from contextlib import contextmanager
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import Field, SecretStr
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.errors import ErrorResponse
from app.contracts.time import UtcTimestamp
from app.modules.identity.http import BrowserAuth
from app.modules.identity.service import utc_now
from app.modules.onboarding.invitations import (
    InvitationStatus,
    exchange_invitation,
    find_invitation,
    invitation_status,
    issue_invitation,
    require_restricted_draft,
    send_invitation,
)
from app.modules.onboarding.schemas import (
    Completion,
    DraftChange,
    DraftData,
    DraftView,
    PrivateInput,
    Revision,
)
from app.modules.onboarding.service import (
    OnboardingError,
    complete_draft,
    draft_view,
    save_draft,
)
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission

RESTRICTED_PATH = "/api/v1/onboarding/convite"
RESTRICTED_COOKIE = "academia_onboarding"


class IssueRequest(PrivateInput):
    solicitacao_id: UUID


class ExchangeRequest(PrivateInput):
    token: SecretStr = Field(min_length=1, max_length=128)


class ExchangeResponse(PrivateInput):
    expira_em: UtcTimestamp


class RestrictedCompletion(PrivateInput):
    revisao: Revision


class RestrictedChange(RestrictedCompletion):
    dados: DraftData


def _browser(request: Request) -> BrowserAuth:
    browser = request.app.state.browser_auth
    if not isinstance(browser, BrowserAuth):
        raise RuntimeError("Adaptador de identidade indisponível.")
    return browser


def invitation_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(tags=["Convites de onboarding"])
    staff_path = "/api/v1/onboarding/clientes/{client_id}/convite"

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except OnboardingError as exc:
            raise HTTPException(exc.status) from None

    @router.post(
        staff_path,
        status_code=201,
        responses={429: {"model": ErrorResponse, "description": "Limite de convites"}},
    )
    def issue(
        client_id: UUID,
        data: IssueRequest,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> InvitationStatus:
        require_permission(actor, Operation.MANAGE_CLIENTS)
        response.headers["Cache-Control"] = "no-store"
        origin = _browser(request).settings.origin
        with transaction() as session:
            invitation_id, mail = issue_invitation(
                session, client_id, actor.user_id, data.solicitacao_id
            )
        if mail is not None:
            send_invitation(get_sessions(), client_id, invitation_id, mail, origin)
        with transaction() as session:
            invitation = find_invitation(session, client_id, invitation_id)
            if invitation is None:
                raise RuntimeError("Convite persistido indisponível.")
            return invitation_status(session, client_id, invitation)

    @router.get(staff_path)
    def status(
        client_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> InvitationStatus:
        require_permission(actor, Operation.MANAGE_CLIENTS)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            invitation = find_invitation(session, client_id)
            if invitation is None:
                raise HTTPException(404)
            return invitation_status(session, client_id, invitation)

    @router.post(RESTRICTED_PATH + "/troca")
    def exchange(
        data: ExchangeRequest, request: Request, response: Response
    ) -> ExchangeResponse:
        browser = _browser(request)
        browser.require_origin(request)
        with transaction() as session:
            secret, expires_at = exchange_invitation(
                session, data.token.get_secret_value()
            )
        response.set_cookie(
            RESTRICTED_COOKIE,
            secret,
            expires=expires_at,
            path=RESTRICTED_PATH,
            httponly=True,
            samesite="lax",
            secure=browser.settings.secure_cookie,
        )
        response.headers["Cache-Control"] = "no-store"
        return ExchangeResponse(expira_em=expires_at)

    @router.get(RESTRICTED_PATH + "/rascunho", response_model_exclude_unset=True)
    def read_draft(request: Request, response: Response) -> DraftView:
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            _, draft = require_restricted_draft(
                session, request.cookies.get(RESTRICTED_COOKIE, "")
            )
            return draft_view(draft)

    @router.patch(RESTRICTED_PATH + "/rascunho", response_model_exclude_unset=True)
    def edit_draft(
        data: RestrictedChange, request: Request, response: Response
    ) -> DraftView:
        _browser(request).require_origin(request)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            _, draft = require_restricted_draft(
                session, request.cookies.get(RESTRICTED_COOKIE, "")
            )
            return save_draft(
                session,
                draft.cliente_id,
                draft.cliente_id,
                DraftChange(versao_base=None, revisao=data.revisao, dados=data.dados),
            )

    @router.post(
        RESTRICTED_PATH + "/conclusao", status_code=204, response_class=Response
    )
    def complete(data: RestrictedCompletion, request: Request) -> Response:
        browser = _browser(request)
        browser.require_origin(request)
        with transaction() as session:
            invitation, draft = require_restricted_draft(
                session, request.cookies.get(RESTRICTED_COOKIE, "")
            )
            complete_draft(
                session,
                draft.cliente_id,
                draft.cliente_id,
                Completion(versao_base=None, revisao=data.revisao),
            )
            invitation.revogado_em = utc_now()
        response = Response(status_code=204, headers={"Cache-Control": "no-store"})
        response.delete_cookie(
            RESTRICTED_COOKIE,
            path=RESTRICTED_PATH,
            httponly=True,
            samesite="lax",
            secure=browser.settings.secure_cookie,
        )
        return response

    return router

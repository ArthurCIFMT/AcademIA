from collections.abc import Callable, Iterator
from contextlib import contextmanager
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.onboarding.schemas import (
    Completion,
    ConfirmUpdate,
    DraftChange,
    DraftView,
    OwnOnboarding,
    SnapshotView,
)
from app.modules.onboarding.service import (
    OnboardingError,
    complete_draft,
    confirm_update,
    get_own,
    get_snapshot,
    save_draft,
)
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


def onboarding_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/onboarding/meu", tags=["Onboarding"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except OnboardingError as exc:
            raise HTTPException(exc.status) from None

    @router.get("", response_model_exclude_unset=True)
    def own(actor: AuthenticatedActor, response: Response) -> OwnOnboarding:
        require_permission(actor, Operation.READ_ONBOARDING, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return get_own(session, actor.user_id)

    @router.get("/versoes/{snapshot_id}")
    def version(
        snapshot_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> SnapshotView:
        require_permission(actor, Operation.READ_ONBOARDING, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            snapshot = get_snapshot(session, actor.user_id, snapshot_id)
            if snapshot is None:
                raise HTTPException(404)
            return snapshot

    @router.patch("/rascunho", response_model_exclude_unset=True)
    def draft(
        data: DraftChange, actor: AuthenticatedActor, response: Response
    ) -> DraftView:
        require_permission(actor, Operation.EDIT_ONBOARDING, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return save_draft(session, actor.user_id, actor.user_id, data)

    @router.post("/conclusao")
    def complete(
        data: Completion, actor: AuthenticatedActor, response: Response
    ) -> SnapshotView:
        require_permission(actor, Operation.EDIT_ONBOARDING, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return complete_draft(session, actor.user_id, actor.user_id, data)

    @router.post("/atualizacoes", status_code=201)
    def update(
        data: ConfirmUpdate, actor: AuthenticatedActor, response: Response
    ) -> SnapshotView:
        require_permission(actor, Operation.EDIT_ONBOARDING, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return confirm_update(session, actor.user_id, actor.user_id, data)

    return router

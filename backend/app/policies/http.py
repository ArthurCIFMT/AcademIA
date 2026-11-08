from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request

from app.modules.identity.http import BrowserAuth
from app.policies.access import Actor, AssignmentReader, Operation, allows


def current_actor(request: Request) -> Actor:
    browser = request.app.state.browser_auth
    if not isinstance(browser, BrowserAuth):
        raise RuntimeError("Adaptador de identidade indisponível.")
    return browser.require_actor(request)


AuthenticatedActor = Annotated[Actor, Depends(current_actor)]


def require_permission(
    actor: Actor,
    operation: Operation,
    *,
    client_id: UUID | None = None,
    assignments: AssignmentReader | None = None,
) -> None:
    if not allows(actor, operation, client_id=client_id, assignments=assignments):
        raise HTTPException(403)

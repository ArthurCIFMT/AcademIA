from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.modules.access.authorization.contracts import DecisionView
from app.modules.access.authorization.service import (
    pending_command,
    record_delivery,
    view_decision,
)
from app.modules.access.integrations.turnstile.client import dispatch
from app.modules.access.integrations.turnstile.contracts import AccessSettings


def deliver_decision(
    sessions: sessionmaker[Session],
    decision_id: UUID,
    settings: AccessSettings,
    clock: Callable[[], datetime],
) -> DecisionView:
    with sessions.begin() as db:
        command = pending_command(db, decision_id, clock())
    if command is not None:
        failure = dispatch(settings, command)
        with sessions.begin() as db:
            record_delivery(db, decision_id, failure)
    with sessions.begin() as db:
        return view_decision(db, decision_id, clock())

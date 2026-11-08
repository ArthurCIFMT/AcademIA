from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.modules.identity.models import Role


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    roles: frozenset[Role]


class Operation(StrEnum):
    MANAGE_ACCOUNTS = "manage_accounts"
    MANAGE_EMPLOYEES = "manage_employees"
    MANAGE_CLIENTS = "manage_clients"
    MANAGE_ASSIGNMENTS = "manage_assignments"
    READ_ONBOARDING = "read_onboarding"
    EDIT_ONBOARDING = "edit_onboarding"
    READ_HEALTH = "read_health"
    RECORD_ASSESSMENT = "record_assessment"
    READ_WORKOUT = "read_workout"
    PRESCRIBE_WORKOUT = "prescribe_workout"
    USE_AI_CONTEXT = "use_ai_context"


class AssignmentReader(Protocol):
    def is_active(self, instructor_id: UUID, client_id: UUID) -> bool:
        """Consulta o vínculo profissional vigente pelo serviço responsável."""
        ...


_ADMINISTRATIVE = {
    Operation.MANAGE_ACCOUNTS: frozenset({Role.ADMINISTRADOR}),
    Operation.MANAGE_EMPLOYEES: frozenset({Role.ADMINISTRADOR}),
    Operation.MANAGE_CLIENTS: frozenset({Role.ADMINISTRADOR, Role.ATENDENTE}),
    Operation.MANAGE_ASSIGNMENTS: frozenset({Role.ADMINISTRADOR}),
}
_OWN = frozenset(
    {
        Operation.READ_ONBOARDING,
        Operation.EDIT_ONBOARDING,
        Operation.READ_HEALTH,
        Operation.READ_WORKOUT,
        Operation.USE_AI_CONTEXT,
    }
)
_ASSIGNED = frozenset(
    {
        Operation.READ_ONBOARDING,
        Operation.READ_HEALTH,
        Operation.RECORD_ASSESSMENT,
        Operation.READ_WORKOUT,
        Operation.PRESCRIBE_WORKOUT,
    }
)


def allows(
    actor: Actor,
    operation: Operation,
    *,
    client_id: UUID | None = None,
    assignments: AssignmentReader | None = None,
) -> bool:
    if operation in _ADMINISTRATIVE:
        return not _ADMINISTRATIVE[operation].isdisjoint(actor.roles)
    if client_id is None:
        return False
    if operation in _OWN and Role.CLIENTE in actor.roles and actor.user_id == client_id:
        return True
    return (
        operation in _ASSIGNED
        and Role.INSTRUTOR in actor.roles
        and assignments is not None
        and assignments.is_active(actor.user_id, client_id)
    )

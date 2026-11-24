from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.people.assignment_directory import AssignmentDirectory
from app.modules.people.profiles import ClientProfile, EmployeeProfile


class MembershipDirectory:
    """Verificações de pessoas e lock compartilhado com alterações cadastrais."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def client_exists(self, client_id: UUID) -> bool:
        return self.session.get(ClientProfile, client_id) is not None

    def lock_people(self, client_id: UUID, attendant_id: UUID) -> None:
        AssignmentDirectory(self.session).lock_people(client_id, attendant_id)

    def client_is_eligible(self, client_id: UUID) -> bool:
        return (
            self.session.scalar(
                select(User.id)
                .join(ClientProfile, ClientProfile.usuario_id == User.id)
                .join(UserRole, UserRole.usuario_id == User.id)
                .where(
                    User.id == client_id,
                    User.estado.in_((AccountState.ATIVO, AccountState.CONVIDADO)),
                    ClientProfile.ativo.is_(True),
                    UserRole.papel == Role.CLIENTE,
                )
            )
            is not None
        )

    def attendant_is_active(self, attendant_id: UUID) -> bool:
        return (
            self.session.scalar(
                select(User.id)
                .join(EmployeeProfile, EmployeeProfile.usuario_id == User.id)
                .join(UserRole, UserRole.usuario_id == User.id)
                .where(
                    User.id == attendant_id,
                    User.estado == AccountState.ATIVO,
                    EmployeeProfile.ativo.is_(True),
                    UserRole.papel == Role.ATENDENTE,
                )
            )
            is not None
        )

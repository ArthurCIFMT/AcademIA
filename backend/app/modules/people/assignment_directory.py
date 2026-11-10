from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.people.profiles import ClientProfile, EmployeeProfile


@dataclass(frozen=True)
class ClientReference:
    id: UUID
    nome: str
    elegivel: bool


@dataclass(frozen=True)
class InstructorReference:
    id: UUID
    nome: str
    email: str


class AssignmentDirectory:
    """Leitura de pessoas e serialização de alterações que afetam designações."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def lock_people(self, *ids: UUID) -> None:
        self.session.execute(
            select(User.id)
            .where(User.id.in_(ids))
            .order_by(User.id)
            .with_for_update(key_share=True)
        ).all()

    def clients(self, ids: list[UUID]) -> dict[UUID, ClientReference]:
        rows = self.session.execute(
            select(
                ClientProfile.usuario_id,
                ClientProfile.nome,
                ClientProfile.ativo,
                User.estado,
            )
            .join(User, User.id == ClientProfile.usuario_id)
            .where(ClientProfile.usuario_id.in_(ids))
        )
        return {
            user_id: ClientReference(
                user_id,
                name,
                active and state in {AccountState.ATIVO, AccountState.CONVIDADO},
            )
            for user_id, name, active, state in rows
        }

    def instructor_names(self, ids: list[UUID]) -> dict[UUID, str]:
        rows = self.session.execute(
            select(EmployeeProfile.usuario_id, EmployeeProfile.nome).where(
                EmployeeProfile.usuario_id.in_(ids)
            )
        )
        return {user_id: name for user_id, name in rows}

    def _instructors(self) -> Select[UUID, str, str]:
        has_role = (
            select(UserRole.id)
            .where(UserRole.usuario_id == User.id, UserRole.papel == Role.INSTRUTOR)
            .exists()
        )
        return (
            select(User.id, EmployeeProfile.nome, User.email)
            .join(EmployeeProfile, EmployeeProfile.usuario_id == User.id)
            .where(
                User.estado == AccountState.ATIVO,
                EmployeeProfile.ativo.is_(True),
                has_role,
            )
        )

    def instructor_is_active(self, user_id: UUID) -> bool:
        return (
            self.session.execute(self._instructors().where(User.id == user_id)).first()
            is not None
        )

    def list_instructors(
        self, search: str, page: int, limit: int
    ) -> tuple[list[InstructorReference], int]:
        base = self._instructors()
        term = search.strip().lower()
        if term:
            base = base.where(
                or_(
                    func.lower(EmployeeProfile.nome).contains(term, autoescape=True),
                    User.email.contains(term, autoescape=True),
                )
            )
        total = (
            self.session.scalar(select(func.count()).select_from(base.subquery())) or 0
        )
        rows = self.session.execute(
            base.order_by(EmployeeProfile.nome, User.id)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return [
            InstructorReference(user_id, name, email) for user_id, name, email in rows
        ], total

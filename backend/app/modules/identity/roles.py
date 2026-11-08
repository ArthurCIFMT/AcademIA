from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.people.profiles import ClientProfile, EmployeeProfile


def effective_roles(session: Session, user_id: UUID) -> frozenset[Role]:
    """Aplica o estado da conta e dos perfis aos papéis cadastrados."""
    roles = session.scalars(
        select(UserRole.papel)
        .join(User, User.id == UserRole.usuario_id)
        .outerjoin(ClientProfile, ClientProfile.usuario_id == User.id)
        .outerjoin(EmployeeProfile, EmployeeProfile.usuario_id == User.id)
        .where(
            User.id == user_id,
            User.estado == AccountState.ATIVO,
            or_(
                and_(UserRole.papel == Role.CLIENTE, ClientProfile.ativo.is_(True)),
                and_(UserRole.papel != Role.CLIENTE, EmployeeProfile.ativo.is_(True)),
            ),
        )
    )
    return frozenset(Role(role) for role in roles)

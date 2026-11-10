from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.people.profiles import ClientProfile, EmployeeProfile


def _eligible_roles() -> Select[str]:
    return (
        select(UserRole.papel)
        .join(User, User.id == UserRole.usuario_id)
        .outerjoin(ClientProfile, ClientProfile.usuario_id == User.id)
        .outerjoin(EmployeeProfile, EmployeeProfile.usuario_id == User.id)
        .where(
            User.estado == AccountState.ATIVO,
            or_(
                and_(UserRole.papel == Role.CLIENTE, ClientProfile.ativo.is_(True)),
                and_(UserRole.papel != Role.CLIENTE, EmployeeProfile.ativo.is_(True)),
            ),
        )
    )


def effective_roles(session: Session, user_id: UUID) -> frozenset[Role]:
    """Aplica o estado da conta e dos perfis aos papéis cadastrados."""
    roles = session.scalars(_eligible_roles().where(UserRole.usuario_id == user_id))
    return frozenset(Role(role) for role in roles)


def active_admin_ids(session: Session) -> list[UUID]:
    statement = (
        _eligible_roles()
        .with_only_columns(UserRole.usuario_id)
        .where(UserRole.papel == Role.ADMINISTRADOR)
        .order_by(UserRole.usuario_id)
    )
    return list(session.scalars(statement))


def lock_admin_changes(session: Session) -> None:
    """Serializa bootstrap e mudanças que podem remover o último administrador."""
    session.execute(select(func.pg_advisory_xact_lock(0x41434144, 1)))

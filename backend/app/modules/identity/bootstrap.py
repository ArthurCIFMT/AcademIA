from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.identity.accounts import create_account, validate_email
from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.people.profiles import EmployeeProfile


class BootstrapConflict(ValueError):
    pass


def bootstrap_admin(
    session: Session,
    *,
    email: str,
    name: str,
    hired_on: date,
    password: str,
    passwords: Passwords,
    now: datetime,
) -> UUID:
    email = validate_email(email)
    name = name.strip()
    if not 1 <= len(name) <= 120:
        raise ValueError("Informe o nome do administrador.")

    # Chave transacional reservada ao bootstrap do AcademIA.
    session.execute(select(func.pg_advisory_xact_lock(0x41434144, 1)))
    admins = session.execute(
        select(User.id, User.email, User.estado, EmployeeProfile.ativo)
        .join(UserRole, UserRole.usuario_id == User.id)
        .outerjoin(EmployeeProfile, EmployeeProfile.usuario_id == User.id)
        .where(UserRole.papel == Role.ADMINISTRADOR)
    ).all()
    for admin_id, admin_email, state, employee_active in admins:
        if admin_email == email and state == AccountState.ATIVO and employee_active:
            return admin_id
    if admins:
        raise BootstrapConflict("O administrador inicial já foi definido.")

    user_id = create_account(
        session,
        email,
        state=AccountState.ATIVO,
        password_hash=passwords.hash(password),
        now=now,
    )
    session.add_all(
        [
            EmployeeProfile(
                usuario_id=user_id,
                nome=name,
                cargo="Administrador",
                data_admissao=hired_on,
                ativo=True,
            ),
            UserRole(id=uuid4(), usuario_id=user_id, papel=Role.ADMINISTRADOR),
        ]
    )
    return user_id

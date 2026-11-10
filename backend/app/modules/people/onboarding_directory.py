from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.people.profiles import ClientProfile


def lock_onboarding_client(session: Session, client_id: UUID) -> date | None:
    """Serializa escritas do onboarding e mudanças no perfil do cliente."""
    return session.scalar(
        select(ClientProfile.data_nascimento)
        .join(User, User.id == ClientProfile.usuario_id)
        .join(UserRole, UserRole.usuario_id == User.id)
        .where(
            User.id == client_id,
            User.estado.in_((AccountState.ATIVO, AccountState.CONVIDADO)),
            ClientProfile.ativo.is_(True),
            UserRole.papel == Role.CLIENTE,
        )
        .with_for_update(of=(User, ClientProfile), key_share=True)
    )

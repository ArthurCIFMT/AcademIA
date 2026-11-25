from collections.abc import Callable
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy.orm import Session, sessionmaker

from app.modules.identity.models import AccountState, Role, User
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor
from app.policies.http import AuthenticatedActor

Address = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
PhotoReader = Callable[[Session, UUID], bytes | None]


class OwnAddress(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endereco: Address | None


class OwnProfileView(BaseModel):
    email: str
    endereco: str | None
    nome_cliente: str | None
    data_nascimento: date | None
    telefone: str | None
    nome_funcionario: str | None
    cargo: str | None
    data_admissao: date | None
    foto_disponivel: bool


def profile_view(
    db: Session, user: User, actor: Actor, read_photo: PhotoReader
) -> OwnProfileView:
    client = db.get(ClientProfile, user.id) if Role.CLIENTE in actor.roles else None
    employee = (
        db.get(EmployeeProfile, user.id) if actor.roles - {Role.CLIENTE} else None
    )
    return OwnProfileView(
        email=user.email,
        endereco=user.endereco,
        nome_cliente=client.nome if client else None,
        data_nascimento=client.data_nascimento if client else None,
        telefone=client.telefone if client else None,
        nome_funcionario=employee.nome if employee else None,
        cargo=employee.cargo if employee else None,
        data_admissao=employee.data_admissao if employee else None,
        foto_disponivel=client is not None and read_photo(db, user.id) is not None,
    )


def active_user(db: Session, actor: Actor, *, lock: bool = False) -> User:
    user = db.get(User, actor.user_id, with_for_update=lock)
    if user is None or user.estado != AccountState.ATIVO or not actor.roles:
        raise HTTPException(403)
    return user


def own_profile_router(
    get_sessions: Callable[[], sessionmaker[Session]], read_photo: PhotoReader
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/meu-perfil", tags=["Meu perfil"])

    @router.get("")
    def own_profile(actor: AuthenticatedActor, response: Response) -> OwnProfileView:
        response.headers["Cache-Control"] = "no-store"
        with get_sessions().begin() as db:
            return profile_view(db, active_user(db, actor), actor, read_photo)

    @router.get(
        "/foto",
        response_class=Response,
        responses={200: {"content": {"image/jpeg": {}}}},
    )
    def own_photo(actor: AuthenticatedActor) -> Response:
        with get_sessions().begin() as db:
            user = active_user(db, actor)
            photo = read_photo(db, user.id) if Role.CLIENTE in actor.roles else None
            if photo is None:
                raise HTTPException(404)
            return Response(
                content=photo,
                media_type="image/jpeg",
                headers={"Cache-Control": "no-store"},
            )

    @router.patch("/endereco")
    def own_address(
        data: OwnAddress, actor: AuthenticatedActor, response: Response
    ) -> OwnProfileView:
        response.headers["Cache-Control"] = "no-store"
        with get_sessions().begin() as db:
            user = active_user(db, actor, lock=True)
            user.endereco = data.endereco or None
            return profile_view(db, user, actor, read_photo)

    return router

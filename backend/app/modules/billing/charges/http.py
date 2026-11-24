from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.billing.charges.schemas import (
    ChargePage,
    ChargeView,
    CreateCharge,
    MembershipChoice,
    OverduePolicy,
    Page,
    RevisionView,
    UpdateCharge,
)
from app.modules.billing.charges.service import (
    ChargeError,
    charge_detail,
    create_charge,
    history,
    list_charges,
    update_charge,
)
from app.modules.identity.models import Role
from app.modules.memberships.service import MembershipError, list_memberships
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission

ADMIN = "/admin/clientes/{client_id}/cobrancas"


def charge_admin(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_CHARGES)
    response.headers["Cache-Control"] = "no-store"
    return actor


Admin = Annotated[Actor, Depends(charge_admin)]
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def charges_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    *,
    policy: OverduePolicy,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["Cobranças"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as db:
                yield db
        except (ChargeError, MembershipError) as exc:
            raise HTTPException(exc.status) from None

    @router.get(ADMIN)
    def index(
        client_id: UUID, _actor: Admin, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> ChargePage:
        with transaction() as db:
            return list_charges(
                db, client_id, page=pagina, limit=limite, now=clock(), policy=policy
            )

    @router.get("/cliente/cobrancas")
    def own(
        actor: AuthenticatedActor,
        response: Response,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> ChargePage:
        if Role.CLIENTE not in actor.roles:
            raise HTTPException(403)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as db:
            return list_charges(
                db, actor.user_id, page=pagina, limit=limite, now=clock(), policy=policy
            )

    @router.get(ADMIN + "/matriculas")
    def membership_choices(
        client_id: UUID,
        _actor: Admin,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> Page[MembershipChoice]:
        with transaction() as db:
            page = list_memberships(
                db, client_id, now=clock(), page=pagina, limit=limite
            )
        return Page[MembershipChoice](
            itens=[
                MembershipChoice(
                    id=item.id,
                    inicio=item.inicio,
                    fim=item.fim,
                    modalidade=item.modalidade_contratada,
                )
                for item in page.itens
            ],
            pagina=page.pagina,
            limite=page.limite,
            total=page.total,
        )

    @router.get(ADMIN + "/{charge_id}")
    def detail(client_id: UUID, charge_id: UUID, _actor: Admin) -> ChargeView:
        with transaction() as db:
            return charge_detail(db, client_id, charge_id, now=clock())

    @router.get(ADMIN + "/{charge_id}/historico")
    def revisions(
        client_id: UUID,
        charge_id: UUID,
        _actor: Admin,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> Page[RevisionView]:
        with transaction() as db:
            return history(db, client_id, charge_id, page=pagina, limit=limite)

    @router.post(ADMIN, status_code=201, responses={200: {"model": ChargeView}})
    def create(
        data: CreateCharge,
        client_id: UUID,
        actor: Admin,
        request: Request,
        response: Response,
    ) -> ChargeView:
        with transaction() as db:
            result, created = create_charge(
                db,
                client_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
                now=clock(),
            )
        response.status_code = 201 if created else 200
        return result

    @router.put(ADMIN + "/{charge_id}")
    def update(
        data: UpdateCharge,
        client_id: UUID,
        charge_id: UUID,
        actor: Admin,
        request: Request,
    ) -> ChargeView:
        with transaction() as db:
            return update_charge(
                db,
                client_id,
                charge_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
                now=clock(),
            )

    return router

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.modules.billing.charges.schemas import Page
from app.modules.billing.payments.checkout import (
    SimulatedReceipt,
    SimulatePurchase,
    SimulationState,
    own_purchase,
    purchase_history,
    simulate_purchase,
)
from app.modules.billing.payments.http import PageNumber, PageSize
from app.modules.billing.payments.service import PaymentError
from app.modules.identity.models import Role
from app.modules.memberships.schemas import MembershipPage, PlanView
from app.modules.memberships.service import list_plans
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def checkout_client(actor: AuthenticatedActor, response: Response) -> Actor:
    if Role.CLIENTE not in actor.roles:
        raise HTTPException(403)
    response.headers["Cache-Control"] = "no-store"
    return actor


CheckoutClient = Annotated[Actor, Depends(checkout_client)]


class LatestSimulatedPurchase(BaseModel):
    plano: str
    estado: SimulationState
    simulado_em: UtcTimestamp


def attendant_checkout_router(
    get_sessions: Callable[[], sessionmaker[Session]],
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/atendimento/clientes", tags=["Compra simulada"])

    @router.get("/{client_id}/ultima-compra-simulada")
    def latest_purchase(
        client_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> LatestSimulatedPurchase | None:
        require_permission(actor, Operation.MANAGE_MEMBERSHIPS)
        response.headers["Cache-Control"] = "no-store"
        with get_sessions().begin() as db:
            purchases = purchase_history(db, client_id, page=1, limit=1).itens
            if not purchases:
                return None
            purchase = purchases[0]
            return LatestSimulatedPurchase(
                plano=purchase.plano_nome_snapshot,
                estado=purchase.estado,
                simulado_em=purchase.simulado_em,
            )

    return router


def simulated_checkout_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/cliente/compra-simulada",
        tags=["Compra simulada de plano"],
    )

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as db:
                yield db
        except PaymentError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/planos")
    def plan_catalog(
        _actor: CheckoutClient, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> MembershipPage[PlanView]:
        with transaction() as db:
            return list_plans(
                db, active_only=True, priced_only=True, page=pagina, limit=limite
            )

    @router.get("")
    def history(
        actor: CheckoutClient, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> Page[SimulatedReceipt]:
        with transaction() as db:
            return purchase_history(db, actor.user_id, page=pagina, limit=limite)

    @router.get("/{purchase_id}")
    def detail(purchase_id: UUID, actor: CheckoutClient) -> SimulatedReceipt:
        with transaction() as db:
            return own_purchase(db, actor.user_id, purchase_id)

    @router.post("", status_code=201, responses={200: {"model": SimulatedReceipt}})
    def simulate(
        data: SimulatePurchase,
        request: Request,
        response: Response,
        actor: CheckoutClient,
    ) -> SimulatedReceipt:
        with transaction() as db:
            result, created = simulate_purchase(
                db,
                actor.user_id,
                data,
                correlation=request.state.correlation_id,
                now=clock(),
            )
        response.status_code = 201 if created else 200
        return result

    return router

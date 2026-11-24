from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.billing.payments.schemas import (
    CorrectPayment,
    PaymentPage,
    PaymentView,
    RegisterPayment,
    VoidPayment,
)
from app.modules.billing.payments.service import (
    PaymentError,
    list_payments,
    record_payment,
    void_payment,
)
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def payment_admin(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_MANUAL_PAYMENTS)
    response.headers["Cache-Control"] = "no-store"
    return actor


PaymentAdmin = Annotated[Actor, Depends(payment_admin)]
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def manual_payments_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/admin/clientes/{client_id}/pagamentos",
        tags=["Pagamentos manuais"],
    )

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as db:
                yield db
        except PaymentError as exc:
            raise HTTPException(exc.status) from None

    @router.get("")
    def history(
        client_id: UUID,
        _actor: PaymentAdmin,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> PaymentPage:
        with transaction() as db:
            return list_payments(db, client_id, page=pagina, limit=limite)

    def save(
        client_id: UUID,
        data: RegisterPayment,
        request: Request,
        response: Response,
        actor: Actor,
        replaced_id: UUID | None = None,
    ) -> PaymentView:
        with transaction() as db:
            view, created = record_payment(
                db,
                client_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
                now=clock(),
                replaced_id=replaced_id,
            )
        response.status_code = 201 if created else 200
        return view

    @router.post("", status_code=201, responses={200: {"model": PaymentView}})
    def register(
        client_id: UUID,
        data: RegisterPayment,
        request: Request,
        response: Response,
        actor: PaymentAdmin,
    ) -> PaymentView:
        return save(client_id, data, request, response, actor)

    @router.post(
        "/{payment_id}/correcao",
        status_code=201,
        responses={200: {"model": PaymentView}},
    )
    def correct(
        client_id: UUID,
        payment_id: UUID,
        data: CorrectPayment,
        request: Request,
        response: Response,
        actor: PaymentAdmin,
    ) -> PaymentView:
        return save(client_id, data, request, response, actor, payment_id)

    @router.post("/{payment_id}/anulacao")
    def annul(
        client_id: UUID,
        payment_id: UUID,
        data: VoidPayment,
        request: Request,
        actor: PaymentAdmin,
    ) -> PaymentView:
        with transaction() as db:
            return void_payment(
                db,
                client_id,
                payment_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
                now=clock(),
            )

    return router

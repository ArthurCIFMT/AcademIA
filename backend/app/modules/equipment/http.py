from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session, sessionmaker
from starlette.types import Message

from app.contracts.errors import ErrorResponse
from app.modules.equipment.images import (
    MAX_IMAGE_BASE64,
    EquipmentImageStorage,
    InvalidEquipmentImage,
    LocalEquipmentImages,
    normalize_image,
)
from app.modules.equipment.service import (
    ADMIN_PATH,
    PUBLIC_PATH,
    EquipmentAdmin,
    EquipmentCreate,
    EquipmentError,
    EquipmentPage,
    EquipmentPublic,
    EquipmentUpdate,
    admin_view,
    catalog,
    create_equipment,
    equipment_row,
    inventory,
    update_equipment,
)
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission

MAX_WRITE_BYTES = MAX_IMAGE_BASE64 + 16_384
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]
IMAGE_RESPONSE: dict[int | str, dict[str, object]] = {
    200: {"content": {"image/png": {}}}
}
WRITE_ERRORS: dict[int | str, dict[str, object]] = {
    413: {"model": ErrorResponse, "description": "Corpo acima do limite de tamanho"}
}


class EquipmentRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[object, object, Response]]:
        handler = super().get_route_handler()

        async def limited(request: Request) -> Response:
            received = 0

            async def receive() -> Message:
                nonlocal received
                message = await request.receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > MAX_WRITE_BYTES:
                        raise HTTPException(413)
                return message

            if request.method in {"POST", "PUT"}:
                return await handler(Request(request.scope, receive=receive))
            return await handler(request)

        return limited


def equipment_admin(actor: AuthenticatedActor, response: Response) -> None:
    require_permission(actor, Operation.MANAGE_EQUIPMENT)
    response.headers["Cache-Control"] = "no-store"


def equipment_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    images: EquipmentImageStorage | None = None,
) -> APIRouter:
    storage = (
        images
        if images is not None
        else LocalEquipmentImages(
            Path(environ.get("ACADEMIA_EQUIPMENT_IMAGES_DIR", "uploads/equipamentos"))
        )
    )
    public = APIRouter(prefix=PUBLIC_PATH, tags=["Equipamentos"])
    admin = APIRouter(
        prefix=ADMIN_PATH,
        tags=["Inventário"],
        dependencies=[Depends(equipment_admin)],
        route_class=EquipmentRoute,
    )

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except EquipmentError as exc:
            raise HTTPException(exc.status) from None
        except InvalidEquipmentImage:
            raise HTTPException(422) from None

    def save_image(encoded: str | None) -> str | None:
        return storage.store(normalize_image(encoded)) if encoded is not None else None

    def image_response(equipment_id: UUID, *, offered: bool) -> Response:
        with transaction() as session:
            reference = equipment_row(session, equipment_id, public=offered).imagem_ref
            image = storage.read(reference) if reference else None
        if image is None:
            raise HTTPException(404)
        return Response(
            image,
            media_type="image/png",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    @public.get("")
    def available(
        response: Response, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> EquipmentPage[EquipmentPublic]:
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return catalog(session, pagina, limite)

    @public.get(
        "/{equipment_id}/imagem", response_class=Response, responses=IMAGE_RESPONSE
    )
    def offered_image(equipment_id: UUID) -> Response:
        return image_response(equipment_id, offered=True)

    @admin.get("")
    def list_inventory(
        pagina: PageNumber = 1, limite: PageSize = 20
    ) -> EquipmentPage[EquipmentAdmin]:
        with transaction() as session:
            return inventory(session, pagina, limite)

    @admin.get("/{equipment_id}")
    def detail(equipment_id: UUID) -> EquipmentAdmin:
        with transaction() as session:
            return admin_view(equipment_row(session, equipment_id))

    @admin.get(
        "/{equipment_id}/imagem", response_class=Response, responses=IMAGE_RESPONSE
    )
    def inventory_image(equipment_id: UUID) -> Response:
        return image_response(equipment_id, offered=False)

    @admin.post("", status_code=201, responses=WRITE_ERRORS)
    def create(data: EquipmentCreate) -> EquipmentAdmin:
        with transaction() as session:
            return admin_view(
                create_equipment(session, data, save_image(data.imagem_base64))
            )

    @admin.put("/{equipment_id}", responses=WRITE_ERRORS)
    def update(equipment_id: UUID, data: EquipmentUpdate) -> EquipmentAdmin:
        with transaction() as session:
            row = equipment_row(session, equipment_id, lock=True)
            if row.revision != data.revisao:
                raise EquipmentError(409)
            update_equipment(row, data, save_image(data.imagem_base64))
            return admin_view(row)

    router = APIRouter()
    router.include_router(public)
    router.include_router(admin)
    return router

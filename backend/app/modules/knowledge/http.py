from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session, sessionmaker
from starlette.types import Message

from app.modules.knowledge.catalog import import_initial
from app.modules.knowledge.schemas import (
    MAX_BASE64,
    Decision,
    ImportResult,
    Page,
    RegisterDocument,
    VersionView,
)
from app.modules.knowledge.service import (
    CorpusError,
    authorize,
    decide,
    history,
    register,
    row_by_id,
    view,
)
from app.modules.knowledge.storage import CorpusStorage, InvalidFile, decode_file
from app.policies.http import AuthenticatedActor


class LimitedRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[object, object, Response]]:
        handler = super().get_route_handler()

        async def limited(request: Request) -> Response:
            if request.method in {"POST", "PUT"}:
                received = 0

                async def receive() -> Message:
                    nonlocal received
                    message = await request.receive()
                    if message["type"] == "http.request":
                        received += len(message.get("body", b""))
                        if received > MAX_BASE64 + 65536:
                            raise HTTPException(413)
                    return message

                return await handler(Request(request.scope, receive=receive))
            return await handler(request)

        return limited


def curator(actor: AuthenticatedActor, response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    try:
        authorize(actor)
    except CorpusError as exc:
        raise HTTPException(exc.status) from None


def corpus_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/corpus",
        tags=["Curadoria do corpus"],
        dependencies=[Depends(curator)],
        route_class=LimitedRoute,
    )
    storage = CorpusStorage()

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except CorpusError as exc:
            raise HTTPException(exc.status) from None
        except InvalidFile:
            raise HTTPException(409) from None

    @router.get("")
    def list_versions(
        actor: AuthenticatedActor,
        pagina: Annotated[int, Query(ge=1, le=1000000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
        ambiente: Literal["LITERATURA", "TESTE"] | None = None,
    ) -> Page:
        with transaction() as session:
            return history(session, actor, pagina, limite, ambiente)

    @router.post("", status_code=201)
    def upload(
        data: RegisterDocument, actor: AuthenticatedActor, request: Request
    ) -> VersionView:
        try:
            content = decode_file(data.arquivo_base64, data.formato)
            reference, digest = storage.store(content, data.formato)
        except InvalidFile:
            raise HTTPException(422) from None
        with transaction() as session:
            row, _ = register(
                session,
                actor,
                data.catalogo_id,
                data.ambiente,
                data.metadados,
                data.formato,
                len(content),
                reference,
                digest,
                request.state.correlation_id,
            )
            return row

    @router.post("/importacao-inicial")
    def initial(actor: AuthenticatedActor, request: Request) -> ImportResult:
        with transaction() as session:
            return import_initial(session, actor, storage, request.state.correlation_id)

    @router.get("/{version_id}")
    def detail(version_id: UUID) -> VersionView:
        with transaction() as session:
            return view(session, row_by_id(session, version_id))

    @router.post("/{version_id}/decisao")
    def decision(
        version_id: UUID, data: Decision, actor: AuthenticatedActor, request: Request
    ) -> VersionView:
        with transaction() as session:
            return decide(
                session, actor, version_id, data, storage, request.state.correlation_id
            )

    @router.get("/{version_id}/arquivo", response_class=Response)
    def download(version_id: UUID) -> Response:
        with transaction() as session:
            row = row_by_id(session, version_id)
            content = storage.read(row.arquivo_ref, row.sha256)
            format = row.formato
        return Response(
            content,
            media_type="application/pdf"
            if format == "PDF"
            else "text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": (
                    f'attachment; filename="documento-{version_id}.{format.lower()}"'
                ),
            },
        )

    return router

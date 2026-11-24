from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp, academy_date
from app.modules.access.attendance.service import attendance_history, current_occupancy
from app.modules.identity.models import Role
from app.modules.people.assignment_directory import AssignmentDirectory
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission

_ACADEMY_ZONE = ZoneInfo("America/Sao_Paulo")
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


class OccupancyView(BaseModel):
    total_presentes: int = Field(ge=0)


class VisitView(BaseModel):
    id: UUID
    entrada_em: UtcTimestamp
    saida_em: UtcTimestamp | None


class AttendanceView(BaseModel):
    cliente_nome: str
    de: date
    ate: date
    itens: list[VisitView]
    total: int
    pagina: int
    limite: int


def access_queries_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(tags=["Frequência e lotação"])

    def history(
        client_id: UUID,
        response: Response,
        de: date | None,
        ate: date | None,
        pagina: int,
        limite: int,
    ) -> AttendanceView:
        if de is None and ate is None:
            ate = academy_date(clock())
            de = ate - timedelta(days=29)
        if de is None or ate is None or de > ate or ate == date.max:
            raise HTTPException(422, "Informe as duas datas em ordem válida.")
        # A data final fornecida na tela inclui o dia inteiro no fuso da academia.
        start = datetime.combine(de, time.min, tzinfo=_ACADEMY_ZONE)
        end = datetime.combine(ate + timedelta(days=1), time.min, tzinfo=_ACADEMY_ZONE)
        with get_sessions().begin() as db:
            client = AssignmentDirectory(db).clients([client_id]).get(client_id)
            if client is None:
                raise HTTPException(404)
            result = attendance_history(
                db, client_id, start, end, page=pagina, limit=limite
            )
        response.headers["Cache-Control"] = "no-store"
        return AttendanceView(
            cliente_nome=client.nome,
            de=de,
            ate=ate,
            pagina=pagina,
            limite=limite,
            total=result.total,
            itens=[
                VisitView(
                    id=visit.id, entrada_em=visit.entered_at, saida_em=visit.exited_at
                )
                for visit in result.visits
            ],
        )

    @router.get("/api/v1/acesso/lotacao")
    def occupancy(_actor: AuthenticatedActor, response: Response) -> OccupancyView:
        response.headers["Cache-Control"] = "no-store"
        with get_sessions().begin() as db:
            return OccupancyView(total_presentes=current_occupancy(db))

    @router.get("/api/v1/cliente/frequencia")
    def own_attendance(
        actor: AuthenticatedActor,
        response: Response,
        de: date | None = None,
        ate: date | None = None,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> AttendanceView:
        if Role.CLIENTE not in actor.roles:
            raise HTTPException(403)
        return history(actor.user_id, response, de, ate, pagina, limite)

    @router.get("/api/v1/clientes/{client_id}/frequencia")
    def client_attendance(
        actor: AuthenticatedActor,
        response: Response,
        client_id: UUID,
        de: date | None = None,
        ate: date | None = None,
        pagina: PageNumber = 1,
        limite: PageSize = 20,
    ) -> AttendanceView:
        require_permission(actor, Operation.READ_CLIENT_ATTENDANCE)
        return history(client_id, response, de, ate, pagina, limite)

    return router

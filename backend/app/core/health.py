from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Sistema"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("/health", summary="Verifica se a API está respondendo")
def health() -> HealthResponse:
    return HealthResponse(status="ok")

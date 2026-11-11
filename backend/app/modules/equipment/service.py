from collections.abc import Collection
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
)
from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.equipment.images import MAX_IMAGE_BASE64
from app.modules.equipment.models import Equipment

PUBLIC_PATH = "/api/v1/equipamentos"
ADMIN_PATH = "/api/v1/admin/equipamentos"


class EquipmentFields(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    descricao: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None
    ) = None
    categoria: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] | None
    ) = None
    ativo: StrictBool
    operacional: StrictBool
    imagem_base64: (
        Annotated[str, Field(min_length=1, max_length=MAX_IMAGE_BASE64)] | None
    ) = None

    @field_validator("nome", "descricao", "categoria")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("Texto inválido.")
        return value


class EquipmentCreate(EquipmentFields):
    solicitacao_id: UUID


class EquipmentUpdate(EquipmentFields):
    revisao: Annotated[int, Field(strict=True, ge=1)]


class EquipmentPublic(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    categoria: str | None
    imagem_url: str | None


class EquipmentAdmin(EquipmentPublic):
    ativo: bool
    operacional: bool
    revisao: int


class EquipmentPage[Item](BaseModel):
    itens: list[Item]
    pagina: int
    limite: int
    total: int


class EquipmentError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _offer() -> Select[Equipment]:
    return select(Equipment).where(
        Equipment.ativo.is_(True), Equipment.operacional.is_(True)
    )


def _public(row: Equipment, path: str = PUBLIC_PATH) -> EquipmentPublic:
    return EquipmentPublic(
        id=row.id,
        nome=row.nome,
        descricao=row.descricao,
        categoria=row.categoria,
        imagem_url=f"{path}/{row.id}/imagem?v={row.revision}"
        if row.imagem_ref
        else None,
    )


def admin_view(row: Equipment) -> EquipmentAdmin:
    return EquipmentAdmin(
        **_public(row, ADMIN_PATH).model_dump(),
        ativo=row.ativo,
        operacional=row.operacional,
        revisao=row.revision,
    )


def equipment_row(
    session: Session, equipment_id: UUID, *, public: bool = False, lock: bool = False
) -> Equipment:
    query = (_offer() if public else select(Equipment)).where(
        Equipment.id == equipment_id
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    row = session.scalar(query)
    if row is None:
        raise EquipmentError(404)
    return row


def _page(
    session: Session, query: Select[Equipment], page: int, limit: int
) -> tuple[list[Equipment], int]:
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list(
        session.scalars(
            query.order_by(Equipment.nome, Equipment.id)
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    return rows, total


def catalog(session: Session, page: int, limit: int) -> EquipmentPage[EquipmentPublic]:
    rows, total = _page(session, _offer(), page, limit)
    return EquipmentPage[EquipmentPublic](
        itens=[_public(row) for row in rows], pagina=page, limite=limit, total=total
    )


def inventory(session: Session, page: int, limit: int) -> EquipmentPage[EquipmentAdmin]:
    rows, total = _page(session, select(Equipment), page, limit)
    return EquipmentPage[EquipmentAdmin](
        itens=[admin_view(row) for row in rows], pagina=page, limite=limit, total=total
    )


def _apply(row: Equipment, data: EquipmentFields) -> None:
    row.nome = data.nome
    row.descricao = data.descricao or None
    row.categoria = data.categoria or None
    row.ativo = data.ativo
    row.operacional = data.operacional


def create_equipment(
    session: Session, data: EquipmentCreate, image_ref: str | None
) -> Equipment:
    values = {
        "nome": data.nome,
        "descricao": data.descricao or None,
        "categoria": data.categoria or None,
        "ativo": data.ativo,
        "operacional": data.operacional,
        "imagem_ref": image_ref,
        "revision": 1,
    }
    created = session.scalars(
        insert(Equipment)
        .values(id=data.solicitacao_id, **values)
        .on_conflict_do_nothing(index_elements=[Equipment.id])
        .returning(Equipment)
    ).one_or_none()
    if created is not None:
        return created
    row = equipment_row(session, data.solicitacao_id, lock=True)
    if any(getattr(row, field) != value for field, value in values.items()):
        raise EquipmentError(409)
    return row


def update_equipment(
    row: Equipment, data: EquipmentUpdate, image_ref: str | None
) -> None:
    _apply(row, data)
    if "imagem_base64" in data.model_fields_set:
        row.imagem_ref = image_ref
    row.revision += 1


@dataclass(frozen=True)
class EquipmentResource:
    id: UUID
    nome: str
    ativo: bool
    operacional: bool

    @property
    def disponivel(self) -> bool:
        return self.ativo and self.operacional


class EquipmentUnavailable(Exception):
    def __init__(self, ids: frozenset[UUID]) -> None:
        self.ids = ids


def available_resources(session: Session) -> list[EquipmentResource]:
    rows = session.scalars(
        _offer()
        .order_by(Equipment.nome, Equipment.id)
        .execution_options(populate_existing=True)
    )
    return [
        EquipmentResource(row.id, row.nome, row.ativo, row.operacional) for row in rows
    ]


def read_resources(
    session: Session, ids: Collection[UUID], *, lock: bool = False
) -> dict[UUID, EquipmentResource]:
    if not ids:
        return {}
    query = select(Equipment).where(Equipment.id.in_(ids)).order_by(Equipment.id)
    if lock:
        query = query.with_for_update(read=True)
    return {
        row.id: EquipmentResource(row.id, row.nome, row.ativo, row.operacional)
        for row in session.scalars(query.execution_options(populate_existing=True))
    }


def require_available(session: Session, ids: Collection[UUID]) -> None:
    """Revalida a combinação escolhida na transação que publicará a ficha."""
    requested = frozenset(ids)
    resources = read_resources(session, requested, lock=True)
    unavailable = requested - {
        resource.id for resource in resources.values() if resource.disponivel
    }
    if unavailable:
        raise EquipmentUnavailable(unavailable)

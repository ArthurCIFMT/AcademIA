from datetime import UTC, datetime
from typing import Annotated, Self, cast
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
    model_validator,
)
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.contracts.time import UtcTimestamp
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.classes.models import ClassOccurrence, ClassState


def iso_timestamp(value: object, handler: ValidatorFunctionWrapHandler) -> datetime:
    if not isinstance(value, (str, datetime)):
        raise ValueError("Informe data e hora em ISO 8601 com fuso.")
    if isinstance(value, str) and "T" not in value:
        raise ValueError("Informe data e hora em ISO 8601 com fuso.")
    try:
        return cast(datetime, handler(value))
    except OverflowError:
        raise ValueError("A data está fora do intervalo suportado em UTC.") from None


ClassTimestamp = Annotated[UtcTimestamp, WrapValidator(iso_timestamp)]


class ClassFields(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    descricao: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None
    ) = None
    inicio: ClassTimestamp
    fim: ClassTimestamp

    @field_validator("nome", "descricao")
    @classmethod
    def valid_text(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("Texto inválido.")
        return value or None

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        if self.fim <= self.inicio:
            raise ValueError("O fim deve ocorrer depois do início.")
        return self


class CreateClass(ClassFields):
    solicitacao_id: UUID


class ClassRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revisao: Annotated[int, Field(strict=True, ge=1)]


class UpdateClass(ClassFields, ClassRevision):
    pass


class PublicClass(BaseModel):
    id: UUID
    nome: str
    inicio: UtcTimestamp
    fim: UtcTimestamp
    descricao: str | None


class ManagedClass(PublicClass):
    estado: ClassState
    revisao: int


class ClassPage[Item](BaseModel):
    itens: list[Item]
    pagina: int
    limite: int
    total: int


class ClassError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _public(row: ClassOccurrence) -> PublicClass:
    return PublicClass(
        id=row.id,
        nome=row.nome,
        inicio=row.inicio,
        fim=row.fim,
        descricao=row.descricao,
    )


def _managed(row: ClassOccurrence) -> ManagedClass:
    return ManagedClass(
        **_public(row).model_dump(), estado=ClassState(row.estado), revisao=row.revision
    )


def public_schedule(
    db: Session, *, now: datetime, page: int, limit: int
) -> ClassPage[PublicClass]:
    query = select(ClassOccurrence).where(
        ClassOccurrence.estado == ClassState.AGENDADA, ClassOccurrence.fim > now
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(ClassOccurrence.inicio, ClassOccurrence.id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return ClassPage(
        itens=[_public(row) for row in rows], pagina=page, limite=limit, total=total
    )


def admin_schedule(db: Session, *, page: int, limit: int) -> ClassPage[ManagedClass]:
    total = db.scalar(select(func.count()).select_from(ClassOccurrence)) or 0
    rows = db.scalars(
        select(ClassOccurrence)
        .order_by(ClassOccurrence.inicio.desc(), ClassOccurrence.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return ClassPage(
        itens=[_managed(row) for row in rows], pagina=page, limite=limit, total=total
    )


def _audit(
    db: Session, occurrence_id: UUID, actor_id: UUID, correlation: UUID, action: str
) -> None:
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            resource_type="aula_ocorrencia",
            resource_id=occurrence_id,
            correlation_id=correlation,
            occurred_at=datetime.now(UTC),
        ),
    )


def _get_locked(db: Session, occurrence_id: UUID) -> ClassOccurrence:
    row = db.scalar(
        select(ClassOccurrence)
        .where(ClassOccurrence.id == occurrence_id)
        .with_for_update()
    )
    if row is None:
        raise ClassError(404)
    return row


def _same_fields(row: ClassOccurrence, data: ClassFields) -> bool:
    return (row.nome, row.descricao, row.inicio, row.fim) == (
        data.nome,
        data.descricao,
        data.inicio,
        data.fim,
    )


def create_occurrence(
    db: Session, data: CreateClass, *, actor_id: UUID, correlation: UUID
) -> ManagedClass:
    occurrence_id = data.solicitacao_id
    row = db.scalar(
        insert(ClassOccurrence)
        .values(
            id=occurrence_id,
            nome=data.nome,
            inicio=data.inicio,
            fim=data.fim,
            descricao=data.descricao,
            estado=ClassState.AGENDADA,
            revision=1,
        )
        .on_conflict_do_nothing(index_elements=[ClassOccurrence.id])
        .returning(ClassOccurrence)
    )
    if row is None:
        row = _get_locked(db, occurrence_id)
        if row.revision != 1 or not _same_fields(row, data):
            raise ClassError(409)
    else:
        _audit(db, occurrence_id, actor_id, correlation, "class.created")
    return _managed(row)


def update_occurrence(
    db: Session,
    occurrence_id: UUID,
    data: UpdateClass,
    *,
    actor_id: UUID,
    correlation: UUID,
) -> ManagedClass:
    row = _get_locked(db, occurrence_id)
    if row.revision != data.revisao or row.estado != ClassState.AGENDADA:
        raise ClassError(409)
    if not _same_fields(row, data):
        row.nome, row.descricao, row.inicio, row.fim = (
            data.nome,
            data.descricao,
            data.inicio,
            data.fim,
        )
        row.revision += 1
        _audit(db, occurrence_id, actor_id, correlation, "class.updated")
    return _managed(row)


def cancel_occurrence(
    db: Session,
    occurrence_id: UUID,
    data: ClassRevision,
    *,
    actor_id: UUID,
    correlation: UUID,
) -> ManagedClass:
    row = _get_locked(db, occurrence_id)
    if row.revision != data.revisao:
        raise ClassError(409)
    if row.estado == ClassState.AGENDADA:
        row.estado = ClassState.CANCELADA
        row.revision += 1
        _audit(db, occurrence_id, actor_id, correlation, "class.cancelled")
    return _managed(row)

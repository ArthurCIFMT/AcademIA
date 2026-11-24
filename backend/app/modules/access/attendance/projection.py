from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PassageRecord:
    id: UUID
    direction: str
    occurred_at: datetime


@dataclass(frozen=True)
class Visit:
    entry_id: UUID
    exit_id: UUID | None = None


@dataclass(frozen=True)
class Projection:
    visits: tuple[Visit, ...]
    outcomes: dict[UUID, str]


def project(passages: Iterable[PassageRecord]) -> Projection:
    ordered = sorted(
        passages,
        key=lambda row: (row.occurred_at, row.direction != "ENTRADA", row.id),
    )
    visits: list[Visit] = []
    outcomes: dict[UUID, str] = {}
    open_entry = None
    for row in ordered:
        if row.direction == "ENTRADA":
            if open_entry is not None:
                outcomes[row.id] = "ENTRADA_REPETIDA"
                continue
            open_entry = row.id
            outcomes[row.id] = "ENTRADA_REGISTRADA"
        elif row.direction == "SAIDA":
            if open_entry is None:
                outcomes[row.id] = "SAIDA_SEM_ENTRADA"
                continue
            visits.append(Visit(open_entry, row.id))
            open_entry = None
            outcomes[row.id] = "SAIDA_REGISTRADA"
        else:
            raise ValueError("Direção de passagem inválida")
    if open_entry is not None:
        visits.append(Visit(open_entry))
    return Projection(tuple(visits), outcomes)

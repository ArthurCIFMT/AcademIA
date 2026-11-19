"""Carga opt-in, aditiva e repetível para a demonstração acadêmica."""

import argparse
import json
import sys
from pathlib import Path
from typing import Annotated, Self
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import (
    DatabaseTarget,
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.equipment.service import (
    EquipmentCreate,
    create_equipment,
    inventory,
)
from app.modules.identity.models import Role
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.training.catalog import catalog_page, create_exercise
from app.modules.training.schemas import ExerciseFields, normalize_name

CATALOG = (
    Path(__file__).resolve().parents[2] / "database/seeds/catalogo-demonstracao-v1.json"
)
MARKER = "seed.catalogo.demonstracao.v1"


class DemoEquipment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chave: Annotated[str, Field(min_length=1)]
    nome: str
    categoria: str
    descricao: str


class DemoExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str
    descricao: str
    grupo_muscular: str
    dispensa_equipamento: bool
    combinacoes: list[list[str]]

    def fields(self, resources: dict[str, UUID]) -> ExerciseFields:
        return ExerciseFields(
            nome=self.nome,
            descricao=self.descricao,
            grupo_muscular=self.grupo_muscular,
            ativo=True,
            dispensa_equipamento=self.dispensa_equipamento,
            combinacoes=[
                [resources[key] for key in group] for group in self.combinacoes
            ],
        )


class DemoCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao: Annotated[int, Field(strict=True, ge=1, le=1)]
    finalidade: str
    equipamentos: Annotated[list[DemoEquipment], Field(min_length=1)]
    exercicios: Annotated[list[DemoExercise], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        resources = {
            item.chave: uuid5(NAMESPACE_URL, f"{MARKER}/{item.chave}")
            for item in self.equipamentos
        }
        names = [normalize_name(item.nome) for item in self.equipamentos]
        if len(resources) != len(self.equipamentos) or len(set(names)) != len(names):
            raise ValueError("Equipamentos duplicados na carga de demonstração.")
        names = [normalize_name(item.nome) for item in self.exercicios]
        if len(set(names)) != len(names):
            raise ValueError("Exercícios duplicados na carga de demonstração.")
        for equipment in self.equipamentos:
            EquipmentCreate(
                nome=equipment.nome,
                categoria=equipment.categoria,
                descricao=equipment.descricao,
                ativo=True,
                operacional=True,
                solicitacao_id=resources[equipment.chave],
            )
        for exercise in self.exercicios:
            if any(
                key not in resources for group in exercise.combinacoes for key in group
            ):
                raise ValueError("Exercício referencia recurso ausente na carga.")
            fields = exercise.fields(resources)
            if not fields.dispensa_equipamento and not fields.combinacoes:
                raise ValueError("Exercício sem declaração de recursos.")
        return self


def load_catalog(path: Path = CATALOG) -> DemoCatalog:
    return DemoCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def seed_catalog(session: Session, actor_id: UUID, data: DemoCatalog) -> dict[str, int]:
    if Role.ADMINISTRADOR not in effective_roles(session, actor_id):
        raise ValueError("Informe um administrador ativo para executar a carga.")
    check_database(session.connection(), _target(session))
    # Uma repetição concorrente não cria um segundo catálogo.
    session.execute(select(func.pg_advisory_xact_lock(0x41434144, 19)))
    result = {
        "equipamentos_criados": 0,
        "equipamentos_preservados": 0,
        "exercicios_criados": 0,
        "exercicios_preservados": 0,
    }
    available: dict[str, UUID] = {}
    existing_ids: set[UUID] = set()
    page = 1
    while True:
        batch = inventory(session, page, 100)
        for saved in batch.itens:
            existing_ids.add(saved.id)
            key = normalize_name(saved.nome)
            available.setdefault(key, saved.id)
        if page * batch.limite >= batch.total:
            break
        page += 1
    resources: dict[str, UUID] = {}
    correlation = uuid4()
    for item in data.equipamentos:
        name = normalize_name(item.nome)
        seed_id = uuid5(NAMESPACE_URL, f"{MARKER}/{item.chave}")
        if seed_id in existing_ids:
            resources[item.chave] = seed_id
            result["equipamentos_preservados"] += 1
            continue
        if name in available:
            resources[item.chave] = available[name]
            result["equipamentos_preservados"] += 1
            continue
        row = create_equipment(
            session,
            EquipmentCreate(
                nome=item.nome,
                categoria=item.categoria,
                descricao=item.descricao,
                ativo=True,
                operacional=True,
                solicitacao_id=seed_id,
            ),
            image_ref=None,
        )
        record_audit(
            session,
            AuditEvent(
                id=uuid4(),
                actor_id=actor_id,
                action="equipment.created",
                resource_type="equipamento",
                resource_id=row.id,
                reason_code=MARKER,
                correlation_id=correlation,
                occurred_at=utc_now(),
            ),
        )
        resources[item.chave] = row.id
        result["equipamentos_criados"] += 1
    existing: set[str] = set()
    page = 1
    while True:
        exercises = catalog_page(session, page, 100)
        existing.update(normalize_name(row.nome) for row in exercises.itens)
        if page * exercises.limite >= exercises.total:
            break
        page += 1
    for exercise in data.exercicios:
        if normalize_name(exercise.nome) in existing:
            result["exercicios_preservados"] += 1
            continue
        create_exercise(session, exercise.fields(resources), actor_id, correlation)
        result["exercicios_criados"] += 1
    return result


def _target(session: Session) -> DatabaseTarget:
    # Esta verificação também permite as integrações no banco descartável.
    database = session.scalar(select(func.current_database()))
    if database not in {"academia_dev", "academia_test"}:
        raise ValueError("A carga só aceita os bancos locais do projeto.")
    return "dev" if database == "academia_dev" else "test"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=UUID, required=True)
    args = parser.parse_args()
    try:
        data = load_catalog()
        engine = create_database_engine("dev")
        try:
            with create_session_factory(engine).begin() as session:
                result = seed_catalog(session, args.actor, data)
        finally:
            engine.dispose()
    except (ValueError, OSError, SQLAlchemyError):
        print(
            "Carga não aplicada. Confira administrador, arquivo, conexão e migrations.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

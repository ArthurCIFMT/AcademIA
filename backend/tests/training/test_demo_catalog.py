from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.modules.audit.models import AuditRecord
from app.modules.equipment.service import equipment_row, inventory
from app.modules.training.catalog import catalog_page, eligible_exercises
from scripts.seed_catalog import DemoCatalog, load_catalog, seed_catalog
from tests.people.test_staff import admin as admin
from tests.people.test_staff import passwords as passwords


@pytest.fixture
def sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(
                    str(Path(__file__).resolve().parents[3] / "database/alembic.ini")
                )
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield create_session_factory(connection)
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_demo_data_has_explicit_equipment_and_no_prescriptions() -> None:
    data = load_catalog()
    assert len(data.equipamentos) == 16 and len(data.exercicios) == 30
    assert any(item.dispensa_equipamento for item in data.exercicios)
    assert any(len(item.combinacoes) > 1 for item in data.exercicios)
    invalid = data.model_dump()
    invalid["exercicios"][0]["combinacoes"] = [["recurso-inexistente"]]
    with pytest.raises(ValueError, match="recurso ausente"):
        DemoCatalog.model_validate(invalid)


@pytest.mark.integration
def test_demo_seed_repeats_without_overwriting_edits_and_respects_unavailability(
    sessions: sessionmaker[Session], admin: UUID
) -> None:
    data = load_catalog()
    with sessions.begin() as session:
        first = seed_catalog(session, admin, data)
        assert first["equipamentos_criados"] == 16
        assert first["exercicios_criados"] == 30
        assert len(eligible_exercises(session)) == 30
        equipment = next(
            item
            for item in inventory(session, 1, 100).itens
            if item.nome == "Esteira ergométrica"
        )
        row = equipment_row(session, equipment.id, lock=True)
        row.operacional = False
        row.nome = "Esteira editada pelo responsável"
        session.flush()
        audit_count = session.scalar(select(func.count()).select_from(AuditRecord))
        second = seed_catalog(session, admin, data)
        assert second == {
            "equipamentos_criados": 0,
            "equipamentos_preservados": 16,
            "exercicios_criados": 0,
            "exercicios_preservados": 30,
        }
        session.refresh(row)
        assert row.nome == "Esteira editada pelo responsável" and not row.operacional
        assert (
            session.scalar(select(func.count()).select_from(AuditRecord)) == audit_count
        )
        assert inventory(session, 1, 100).total == 16
        assert catalog_page(session, 1, 100).total == 30
        assert len(eligible_exercises(session)) == 29


@pytest.mark.integration
def test_demo_seed_reuses_existing_names_and_does_not_change_their_content(
    sessions: sessionmaker[Session], admin: UUID
) -> None:
    data = load_catalog()
    with sessions.begin() as session:
        seed_catalog(session, admin, data)
        changed = data.model_copy(deep=True)
        changed.exercicios[0].nome = "  CAMINHADA   NA ESTEIRA "
        changed.exercicios[0].descricao = "Texto que não deve substituir o existente."
        assert seed_catalog(session, admin, changed)["exercicios_criados"] == 0
        stored = next(
            item
            for item in catalog_page(session, 1, 100).itens
            if item.nome == "Caminhada na esteira"
        )
        assert stored.descricao == data.exercicios[0].descricao


@pytest.mark.integration
def test_demo_seed_requires_an_active_administrator(
    sessions: sessionmaker[Session],
) -> None:
    with sessions.begin() as session:
        with pytest.raises(ValueError, match="administrador ativo"):
            seed_catalog(session, uuid4(), load_catalog())
        assert inventory(session, 1, 100).total == 0

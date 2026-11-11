from collections.abc import Iterator
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.knowledge.ingestion.contracts import State
from app.modules.knowledge.ingestion.service import ExtractionError, Extractor
from app.modules.knowledge.schemas import Decision, Metadata
from app.modules.knowledge.service import (
    ApprovedReference,
    approved_references,
    decide,
    is_approved,
    register,
)
from app.modules.knowledge.storage import CorpusStorage
from app.modules.people.profiles import EmployeeProfile
from app.policies.access import Actor

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(str(ROOT / "database/alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield create_session_factory(connection)
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def seed(
    sessions: sessionmaker[Session], storage: CorpusStorage
) -> tuple[Actor, ApprovedReference]:
    with sessions.begin() as session:
        id = create_account(
            session,
            "curador-extracao@example.test",
            state=AccountState.ATIVO,
            password_hash=Passwords().hash("senha-sintetica-extracao"),
            now=utc_now(),
        )
        session.add(UserRole(id=uuid4(), usuario_id=id, papel=Role.ADMINISTRADOR))
        session.add(
            EmployeeProfile(
                usuario_id=id,
                nome="Curador sintético",
                cargo="Administrador",
                ativo=True,
                data_admissao=date(2026, 1, 1),
            )
        )
        session.flush()
        actor = Actor(id, frozenset({Role.ADMINISTRADOR}))
        content = (FIXTURES / "simbolos.pdf").read_bytes()
        ref, sha = storage.store(content, "PDF")
        metadata = Metadata(
            titulo="Literatura sintética",
            origem_url="https://example.test/fonte",
            licenca="Fixture",
            idioma="pt-BR",
            finalidades=["DUVIDAS"],
            limites="Não é evidência científica.",
        )
        row, _ = register(
            session,
            actor,
            "EXTRACAO-001",
            "LITERATURA",
            metadata,
            "PDF",
            len(content),
            ref,
            sha,
            uuid4(),
        )
        return actor, ApprovedReference(row.id, 2, sha, ref, "PDF", metadata)


@pytest.mark.integration
def test_real_approval_revocation_and_test_scope_control_extraction(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    actor, pending = seed(sessions, storage)
    extractor = Extractor(storage, root=tmp_path / "extracoes")

    def check(id: UUID, revision: int) -> bool:
        with sessions.begin() as session:
            return is_approved(session, id, revision)

    with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
        extractor.extract(pending, approval_check=check)
    with sessions.begin() as session:
        decide(
            session,
            actor,
            pending.version_id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )
        ref = approved_references(session)[0]
    result = extractor.extract(ref, approval_check=check)
    assert result.resultado.estado == State.CONCLUIDA
    with sessions.begin() as session:
        decide(
            session,
            actor,
            ref.version_id,
            Decision(revisao=2, estado="REVOGADO", motivo="Ensaio de revogação"),
            storage,
            uuid4(),
        )
        row, _ = register(
            session,
            actor,
            "TESTE-001",
            "TESTE",
            ref.metadata,
            "PDF",
            len((FIXTURES / "simbolos.pdf").read_bytes()),
            ref.reference,
            ref.sha256,
            uuid4(),
        )
        decide(
            session,
            actor,
            row.id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )
        isolated = ApprovedReference(
            row.id, 2, row.sha256, ref.reference, "PDF", ref.metadata
        )
        assert approved_references(session) == []
    for forbidden in (ref, isolated):
        with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
            extractor.extract(forbidden, approval_check=check)
    assert len(list(extractor.root.glob("*.json"))) == 1


@pytest.mark.integration
def test_revocation_in_separate_transaction_during_parser_is_rechecked(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    from app.modules.knowledge.ingestion.contracts import (
        ExtractionPolicy,
        ParsedDocument,
    )
    from app.modules.knowledge.ingestion.process import run_parser

    storage = CorpusStorage(tmp_path / "originais")
    actor, ref = seed(sessions, storage)
    with sessions.begin() as session:
        decide(
            session,
            actor,
            ref.version_id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )

    def check(id: UUID, revision: int) -> bool:
        with sessions.begin() as session:
            return is_approved(session, id, revision)

    def parse_and_revoke(
        content: bytes, format: str, section: str | None, policy: ExtractionPolicy
    ) -> ParsedDocument:
        result = run_parser(content, format, section, policy)
        with sessions.begin() as session:
            decide(
                session,
                actor,
                ref.version_id,
                Decision(
                    revisao=2,
                    estado="REVOGADO",
                    motivo="Revogação concorrente sintética",
                ),
                storage,
                uuid4(),
            )
        return result

    extractor = Extractor(storage, root=tmp_path / "extracoes", parser=parse_and_revoke)
    with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
        extractor.extract(ref, approval_check=check)
    assert not list(extractor.root.glob("*.json"))

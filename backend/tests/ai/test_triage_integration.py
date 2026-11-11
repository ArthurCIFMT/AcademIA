import copy
from datetime import date
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.main import create_app
from app.modules.ai.policies.triage import Policy
from app.modules.ai.triage.contracts import Signals, SummaryData
from app.modules.ai.triage.engine import Engine
from app.modules.ai.triage.service import TriagePermissionError, TriageService
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.audit.models import AuditRecord
from app.modules.equipment.service import EquipmentCreate, create_equipment
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.knowledge.retrieval.contracts import Evidence
from app.modules.onboarding.schemas import (
    Completion,
    ConfirmUpdate,
    DraftChange,
    DraftData,
    OnboardingData,
    SnapshotView,
)
from app.modules.onboarding.service import complete_draft, confirm_update, save_draft
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.modules.training.catalog import create_exercise, update_exercise
from app.modules.training.schemas import ExerciseFields, ExerciseUpdate
from app.policies.access import Actor
from tests.ai.test_triage import BASE, Double
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions

PASSWORD = "senha-sintetica-triagem"
ORIGIN = "https://academia.example.test"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def seed(sessions: sessionmaker[Session]) -> dict[str, Actor]:
    password = Passwords().hash(PASSWORD)
    people = {}
    roles = {
        "cliente": Role.CLIENTE,
        "outro": Role.CLIENTE,
        "admin": Role.ADMINISTRADOR,
        "instrutor": Role.INSTRUTOR,
        "atendente": Role.ATENDENTE,
    }
    with sessions.begin() as session:
        for name, role in roles.items():
            id = create_account(
                session,
                name + "@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=id, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=id,
                        nome=name,
                        data_nascimento=date(1995, 1, 1),
                        ativo=True,
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=id,
                        nome=name,
                        cargo=name,
                        data_admissao=date(2026, 1, 1),
                        ativo=True,
                    )
                )
            people[name] = Actor(id, frozenset({role}))
        session.flush()
    return people


def complete(sessions: sessionmaker[Session], client: Actor) -> SnapshotView:
    with sessions.begin() as session:
        draft = save_draft(
            session,
            client.user_id,
            client.user_id,
            DraftChange(
                versao_base=None, revisao=None, dados=DraftData.model_validate(BASE)
            ),
        )
        return complete_draft(
            session,
            client.user_id,
            client.user_id,
            Completion(versao_base=None, revisao=draft.revisao),
        )


def exercise(
    sessions: sessionmaker[Session], admin: Actor, equipment: bool = False
) -> UUID:
    with sessions.begin() as session:
        combinations = []
        if equipment:
            resource = create_equipment(
                session,
                EquipmentCreate(
                    solicitacao_id=uuid4(),
                    nome="Halteres sintéticos",
                    ativo=True,
                    operacional=True,
                ),
                None,
            )
            combinations = [[resource.id]]
        item = create_exercise(
            session,
            ExerciseFields(
                nome="Exercício sintético",
                descricao="Descrição sintética",
                grupo_muscular="Geral",
                ativo=True,
                dispensa_equipamento=not equipment,
                combinacoes=combinations,
            ),
            admin.user_id,
            uuid4(),
        )
        return item.id


@pytest.mark.integration
def test_authorized_snapshot_catalog_and_minimal_audit(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    snapshot = complete(sessions, people["cliente"])
    analyst = Double()
    service = TriageService(sessions, Engine(analyst))
    empty = service.evaluate(people["cliente"], people["cliente"].user_id)
    assert empty.estado == "ELEGIVEL_PARA_GERACAO" and not empty.geracao_permitida
    exercise(sessions, people["admin"], equipment=True)
    available = service.evaluate(people["cliente"], people["cliente"].user_id)
    assert available.geracao_permitida and available.exercicios_elegiveis == 1
    assert available.snapshot is not None and available.snapshot.id == snapshot.id
    assert analyst.received[0].dados.model_dump(mode="json") == BASE
    for name in ["outro", "admin", "atendente", "instrutor"]:
        with pytest.raises(TriagePermissionError):
            service.evaluate(people[name], people["cliente"].user_id)
    with sessions.begin() as session:
        change_assignment(
            session,
            people["cliente"].user_id,
            ChangeAssignment(instrutor_id=people["instrutor"].user_id, vigente_id=None),
            people["admin"],
            uuid4(),
        )
    assert (
        service.evaluate(people["instrutor"], people["cliente"].user_id).estado
        == "ELEGIVEL_PARA_GERACAO"
    )
    with sessions.begin() as session:
        logs = list(
            session.scalars(
                select(AuditRecord).where(AuditRecord.acao == "ai.triage.checked")
            )
        )
        assert len(logs) == 3 and all(log.motivo == "policy_v1" for log in logs)


@pytest.mark.integration
@pytest.mark.anyio
async def test_authenticated_api_keeps_pending_and_isolates_clients(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = seed(sessions)
    own = complete(sessions, people["cliente"])
    other = complete(sessions, people["outro"])
    exercise(sessions, people["admin"])
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=ORIGIN,
        headers={"Origin": ORIGIN},
    ) as client:
        endpoint = "/api/v1/ia/triagem/preparacao"
        assert (await client.get(endpoint)).status_code == 401
        assert (
            await client.post(
                "/api/v1/auth/login",
                json={"email": "cliente@example.test", "senha": PASSWORD},
            )
        ).status_code == 200
        response = await client.get(
            endpoint,
            params={
                "client_id": str(people["outro"].user_id),
                "onboarding_id": str(other.id),
            },
        )
        assert response.status_code == 200
        value = response.json()
        assert value["snapshot"]["id"] == str(own.id)
        assert (
            value["estado"] is None and value["estado_tecnico"] == "AGUARDANDO_ANALISE"
        )
        assert not value["geracao_permitida"] and "resumo" not in value
        assert (
            response.headers["cache-control"] == "no-store"
            and str(other.id) not in response.text
        )
        assert (
            await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.test", "senha": PASSWORD},
            )
        ).status_code == 200
        assert (await client.get(endpoint)).status_code == 403


@pytest.mark.integration
def test_snapshot_change_during_analysis_requires_new_execution(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    original = complete(sessions, people["cliente"])
    exercise(sessions, people["admin"])

    class Changing(Double):
        def analyze(
            self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
        ) -> Signals:
            data = copy.deepcopy(BASE)
            data["observacoes"] = "Atualização sintética confirmada"
            with sessions.begin() as session:
                confirm_update(
                    session,
                    people["cliente"].user_id,
                    people["cliente"].user_id,
                    ConfirmUpdate(
                        versao_base=original.id,
                        confirmado=True,
                        dados=OnboardingData.model_validate(data),
                    ),
                )
            return Signals(alerta_grave=False, lacuna=False)

    result = TriageService(sessions, Engine(Changing())).evaluate(
        people["cliente"], people["cliente"].user_id
    )
    assert not result.geracao_permitida and result.resumo is None
    assert result.motivos == ["CONTEXTO_SUPERADO"]


@pytest.mark.integration
def test_catalog_change_during_analysis_invalidates_generation(
    sessions: sessionmaker[Session],
) -> None:
    people = seed(sessions)
    complete(sessions, people["cliente"])
    id = exercise(sessions, people["admin"])

    class Changing(Double):
        def analyze(
            self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
        ) -> Signals:
            with sessions.begin() as session:
                update_exercise(
                    session,
                    id,
                    ExerciseUpdate(
                        nome="Exercício sintético",
                        descricao="Descrição sintética",
                        grupo_muscular="Geral",
                        ativo=False,
                        dispensa_equipamento=True,
                        combinacoes=[],
                        revisao=1,
                    ),
                    people["admin"].user_id,
                    uuid4(),
                )
            return Signals(alerta_grave=False, lacuna=False)

    result = TriageService(sessions, Engine(Changing())).evaluate(
        people["cliente"], people["cliente"].user_id
    )
    assert result.estado == "ELEGIVEL_PARA_GERACAO" and not result.geracao_permitida
    assert result.exercicios_elegiveis == 0 and "RECURSOS_ALTERADOS" in result.motivos


@pytest.mark.integration
def test_equipment_unavailable_after_analysis_invalidates_generation(
    sessions: sessionmaker[Session],
) -> None:
    from app.modules.equipment.models import Equipment

    people = seed(sessions)
    complete(sessions, people["cliente"])
    exercise(sessions, people["admin"], equipment=True)

    class Changing(Double):
        def analyze(
            self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
        ) -> Signals:
            with sessions.begin() as session:
                resource = session.scalar(select(Equipment))
                assert resource is not None
                resource.operacional = False
                resource.revision += 1
            return Signals(alerta_grave=False, lacuna=False)

    result = TriageService(sessions, Engine(Changing())).evaluate(
        people["cliente"], people["cliente"].user_id
    )
    assert result.estado == "ELEGIVEL_PARA_GERACAO" and not result.geracao_permitida
    assert result.exercicios_elegiveis == 0 and "RECURSOS_ALTERADOS" in result.motivos


@pytest.mark.integration
def test_permission_revocation_during_analysis_denies_delivery(
    sessions: sessionmaker[Session],
) -> None:
    from app.modules.identity.models import User

    people = seed(sessions)
    complete(sessions, people["cliente"])

    class Revoking(Double):
        def analyze(
            self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
        ) -> Signals:
            with sessions.begin() as session:
                user = session.get(User, people["cliente"].user_id)
                assert user is not None
                user.estado = AccountState.INATIVO
            return Signals(alerta_grave=False, lacuna=False)

    with pytest.raises(TriagePermissionError):
        TriageService(sessions, Engine(Revoking())).evaluate(
            people["cliente"], people["cliente"].user_id
        )

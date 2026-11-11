from email.message import EmailMessage
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.main import create_app
from app.modules.ai.followup import FollowupService, version_context
from app.modules.ai.http import FollowupView, view
from app.modules.assignments.models import Assignment
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.identity.models import Role, UserRole
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.email import EmailDelivery
from app.modules.notifications.models import DeliveryState, Notification
from app.modules.training.publication import (
    record_opinion,
    review_queue,
    send_review_notice,
)
from app.modules.training.review_schemas import ReviewWorkout
from app.modules.training.workouts import WorkoutError
from app.policies.access import Actor
from tests.ai.test_execution import request
from tests.ai.test_generation import Scenario
from tests.ai.test_generation import scenario as scenario
from tests.ai.test_triage_integration import ORIGIN, PASSWORD
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions


class Transport:
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []
        self.state = DeliveryState.FALHOU

    def deliver(self, message: EmailMessage) -> DeliveryState:
        self.messages.append(message)
        return self.state


def assign(sessions: sessionmaker[Session], scenario: Scenario) -> None:
    people, _, _ = scenario
    with sessions.begin() as session:
        change_assignment(
            session,
            people["cliente"].user_id,
            ChangeAssignment(instrutor_id=people["instrutor"].user_id, vigente_id=None),
            people["admin"],
            uuid4(),
        )


@pytest.mark.integration
def test_followup_sources_pending_notice_failure_and_idempotent_resend(
    sessions: sessionmaker[Session], scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    people, service, provider = scenario
    assign(sessions, scenario)
    transport = Transport()
    monkeypatch.setattr(
        "app.modules.training.publication.local_email_delivery",
        lambda _: EmailDelivery(sessions, transport, "academia@example.test"),
    )
    actor = people["cliente"]
    req = request()
    result = service.generate(actor, actor.user_id, req)
    assert result.versao_publicada_id and len(transport.messages) == 1
    follow = FollowupService(sessions)
    for _ in range(2):
        receipt, context = follow.own(actor, req.solicitacao_id)
        assert receipt.estado == "PUBLICADA" and context
        assert context.contexto.treino.parecer.estado == "PENDENTE"
        assert context.contexto.aviso.email_estado == "FALHOU"
        assert context.contexto.aviso.interno_registrado
        assert (
            context.fontes
            and "resumo"
            not in FollowupView(
                execucao=view(receipt), geracao=context
            ).model_dump_json()
        )
    service.generate(actor, actor.user_id, req)
    assert len(provider.calls) == 2 and len(transport.messages) == 1
    with sessions.begin() as session:
        assert review_queue(session, people["instrutor"], 1, 20).total == 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.canal == "INTERNO",
                    Notification.tipo == "TREINO_PARA_AVALIAR",
                )
            )
            == 1
        )
    transport.state = DeliveryState.ENVIADO
    first = send_review_notice(
        sessions,
        people["instrutor"],
        actor.user_id,
        result.versao_publicada_id,
        retry_after=1,
    )
    second = send_review_notice(
        sessions,
        people["instrutor"],
        actor.user_id,
        result.versao_publicada_id,
        retry_after=1,
    )
    assert first == second and first and first.attempts == 2
    assert len(transport.messages) == 2
    with sessions.begin() as session:
        reviewed = record_opinion(
            session,
            people["instrutor"],
            actor.user_id,
            result.versao_publicada_id,
            ReviewWorkout(
                solicitacao_id=uuid4(), estado="REJEITADO", motivo="Conferir a carga"
            ),
            uuid4(),
        )
        assert reviewed.ficha.dias
    _, context = follow.own(actor, req.solicitacao_id)
    assert context and context.contexto.treino.parecer.estado == "REJEITADO"
    from app.modules.identity.service import utc_now
    from app.modules.knowledge.models import DocumentVersion

    with sessions.begin() as session:
        source = session.get(DocumentVersion, context.fontes[0].documento_versao_id)
        assert source
        source.estado = "REVOGADO"
        source.revogado_por = people["admin"].user_id
        source.revogado_em = utc_now()
        source.motivo_revogacao = "Teste de acompanhamento"
        source.revision += 1
    _, changed = follow.own(actor, req.solicitacao_id)
    assert changed and changed.fontes_alteradas and changed.contexto.treino.ficha.dias


@pytest.mark.integration
def test_no_instructor_and_changed_snapshot_do_not_hide_retained_workout(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    from app.modules.onboarding.schemas import ConfirmUpdate, OnboardingData
    from app.modules.onboarding.service import confirm_update, get_current_snapshot
    from tests.ai.test_triage import BASE

    people, service, _ = scenario
    actor = people["cliente"]
    req = request()
    result = service.generate(actor, actor.user_id, req)
    assert result.versao_publicada_id
    with sessions.begin() as session:
        current = get_current_snapshot(session, actor.user_id)
        assert current
        confirm_update(
            session,
            actor.user_id,
            actor.user_id,
            ConfirmUpdate(
                versao_base=current.id,
                confirmado=True,
                dados=OnboardingData.model_validate(
                    {**BASE, "observacoes": "Atualização sintética"}
                ),
            ),
        )
    _, context = FollowupService(sessions).own(actor, req.solicitacao_id)
    assert context and context.contexto.aviso.instrutor_designado_id is None
    assert (
        "ONBOARDING_ATUALIZADO" in context.contexto.pendencias
        and context.contexto.treino.ficha.dias
    )

    from app.modules.equipment.models import Equipment

    with sessions.begin() as session:
        equipment = session.scalar(select(Equipment))
        assert equipment
        equipment.operacional = False
        equipment.revision += 1
    _, changed = FollowupService(sessions).own(actor, req.solicitacao_id)
    assert changed and "CATALOGO_OU_RECURSOS_ALTERADOS" in changed.contexto.pendencias


@pytest.mark.integration
def test_new_assignment_removes_previous_review_access(
    sessions: sessionmaker[Session], scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    people, service, _ = scenario
    assign(sessions, scenario)
    monkeypatch.setattr(
        "app.modules.training.publication.local_email_delivery",
        lambda _: EmailDelivery(sessions, Transport(), "academia@example.test"),
    )
    actor = people["cliente"]
    result = service.generate(actor, actor.user_id, request())
    assert result.versao_publicada_id
    with sessions.begin() as session:
        session.add(
            UserRole(
                id=uuid4(), usuario_id=people["atendente"].user_id, papel=Role.INSTRUTOR
            )
        )
        session.flush()
        reader = session.scalar(select(Assignment).where(Assignment.fim.is_(None)))
        assert reader
        change_assignment(
            session,
            actor.user_id,
            ChangeAssignment(
                instrutor_id=people["atendente"].user_id, vigente_id=reader.id
            ),
            people["admin"],
            uuid4(),
        )
    with sessions.begin() as session:
        with pytest.raises(WorkoutError) as failure:
            version_context(
                session, people["instrutor"], actor.user_id, result.versao_publicada_id
            )
        assert failure.value.status == 403
        new = Actor(people["atendente"].user_id, frozenset({Role.INSTRUTOR}))
        assert (
            version_context(
                session, new, actor.user_id, result.versao_publicada_id
            ).contexto.treino.ficha.id
            == result.versao_publicada_id
        )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.integration
@pytest.mark.anyio
async def test_followup_api_owns_execution_and_reviewer_is_assigned(
    sessions: sessionmaker[Session], scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    people, service, _ = scenario
    actor = people["cliente"]
    req = request()
    result = service.generate(actor, actor.user_id, req)
    assign(sessions, scenario)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )
    path = "/api/v1/ia/fichas/execucoes/" + str(req.solicitacao_id) + "/acompanhamento"
    version = (
        f"/api/v1/ia/fichas/clientes/{actor.user_id}/versoes/"
        f"{result.versao_publicada_id}/contexto"
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=ORIGIN,
        headers={"Origin": ORIGIN},
    ) as client:
        assert (await client.get(path)).status_code == 401
        for name, expected in [("cliente", 200), ("outro", 404), ("instrutor", 403)]:
            assert (
                await client.post(
                    "/api/v1/auth/login",
                    json={"email": name + "@example.test", "senha": PASSWORD},
                )
            ).status_code == 200
            response = await client.get(path)
            assert response.status_code == expected
            if expected == 200:
                assert (
                    response.headers["cache-control"] == "no-store"
                    and "resumo" not in response.text
                )
        assert (await client.get(version)).status_code == 200
        await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.test", "senha": PASSWORD},
        )
        assert (await client.get(version)).status_code == 403

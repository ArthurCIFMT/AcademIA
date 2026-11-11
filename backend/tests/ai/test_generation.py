import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config as AlembicConfig
from alembic.migration import MigrationContext
from pydantic import SecretStr
from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.adapters.groq import GroqAdapter
from app.modules.ai.generation import GenerationService
from app.modules.ai.orchestration.settings import Config, GroqSettings
from app.modules.ai.persistence.models import Execution, TriageRecord
from app.modules.ai.persistence.state import PostgresState
from app.modules.ai.ports.execution import ExecutionConflict
from app.modules.knowledge.ingestion.indexing import Indexer
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Decision, Metadata
from app.modules.knowledge.service import approved_references, decide, register
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from app.modules.training.publication import published_workout
from app.modules.training.workout_models import WorkoutVersion
from app.policies.access import Actor
from tests.ai.test_execution import request
from tests.ai.test_triage_integration import complete, exercise, seed
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions
from tests.knowledge.test_indexing import synthetic
from tests.knowledge.test_retrieval import QueryDouble


class Provider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.hook: Callable[[], None] = lambda: None
        self.invalid = False

    def handle(self, req: httpx.Request) -> httpx.Response:
        raw = json.loads(req.content)
        payload = json.loads(raw["messages"][1]["content"])["dados_nao_confiaveis"]
        self.calls.append(payload)
        self.hook()
        result: dict[str, Any]
        if "politica" in payload:
            result = {
                "alerta_grave": False,
                "lacuna": False,
                "atualizacao_onboarding_necessaria": False,
            }
        else:
            candidate = payload["candidatos"][0]
            result = {
                "idioma": "pt-BR",
                "dias": [
                    {
                        "titulo": "Dia A",
                        "itens": [
                            {
                                "exercicio_id": str(uuid4())
                                if self.invalid
                                else candidate["id"],
                                "equipamento_ids": candidate["combinacoes_disponiveis"][
                                    0
                                ],
                                "ordem": 1,
                                "series": 3,
                                "repeticoes": "8-12",
                                "carga_kg": None,
                                "cadencia": None,
                                "intervalo_segundos": 60,
                                "observacoes": "",
                            }
                        ],
                    }
                ],
                "explicacao": "Proposta sintética com literatura de teste.",
                "evidencias_ids": [payload["evidencias"][0]["fragmento_id"]],
            }
        return httpx.Response(
            200,
            json={
                "model": Config.load().model,
                "choices": [
                    {
                        "message": {"role": "assistant", "content": json.dumps(result)},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
            },
        )


Scenario = tuple[dict[str, Actor], GenerationService, Provider]


@pytest.fixture
def scenario(sessions: sessionmaker[Session], tmp_path: Path) -> Iterator[Scenario]:
    people = seed(sessions)
    complete(sessions, people["cliente"])
    exercise(sessions, people["admin"], equipment=True)
    storage, reference, _, selection = synthetic(tmp_path)
    metadata = Metadata.model_validate(
        {**reference.metadata.model_dump(), "finalidades": ["TRIAGEM", "GERACAO_GERAL"]}
    )
    with sessions.begin() as session:
        row, _ = register(
            session,
            people["admin"],
            "GEN-001",
            "LITERATURA",
            metadata,
            "TXT",
            len(storage.read(reference.reference, reference.sha256)),
            reference.reference,
            reference.sha256,
            uuid4(),
        )
        decide(
            session,
            people["admin"],
            row.id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )
        ref = approved_references(session)[0]
    extraction = Extractor(storage, root=tmp_path / "extraction", parser=parse).extract(
        ref, approval_check=lambda *_: True
    )
    encoder = QueryDouble()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    for purpose in ["TRIAGEM", "GERACAO_GERAL"]:
        Indexer(sessions, store, encoder, lock_root=tmp_path / "locks").run(
            people["admin"],
            extraction,
            selection.model_copy(update={"finalidade": purpose}),
        )
    provider = Provider()
    adapter = GroqAdapter(
        Config.load(),
        GroqSettings(api_key=SecretStr("synthetic-test-key")),
        transport=httpx.MockTransport(provider.handle),
    )
    evidence = RagEvidence(Retriever(sessions, store, encoder), sessions, store.check)
    service = GenerationService(sessions, llm=adapter, evidence=evidence)
    try:
        yield people, service, provider
    finally:
        adapter.close()
        store.close()


@pytest.mark.integration
def test_real_database_publication_pending_replay_and_no_duplicate_content(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    req = request()
    result = service.generate(actor, actor.user_id, req)
    assert result.estado == "PUBLICADA" and result.versao_publicada_id
    assert result.proposta is None and len(provider.calls) == 2
    assert sum(c.chamadas_fisicas for c in result.consumo) == 2
    assert sum(c.uso.total_tokens for c in result.consumo if c.uso) == 300
    assert service.generate(actor, actor.user_id, req) == result
    assert service.status(actor, req.solicitacao_id) == result
    with sessions.begin() as session:
        published = published_workout(session, actor, actor.user_id)
        assert published and published.parecer.estado == "PENDENTE"
        assert published.ficha.origem == "IA" and published.ficha.explicacao
        row = session.scalar(select(Execution))
        assert row and "proposta" not in row.resultado
        assert session.scalar(select(func.count()).select_from(TriageRecord)) == 1
        assert session.scalar(select(func.count()).select_from(WorkoutVersion)) == 1
    with pytest.raises(ExecutionConflict):
        service.generate(
            actor,
            actor.user_id,
            req.model_copy(update={"mensagem": "Entrada diferente"}),
        )
    assert len(provider.calls) == 2


@pytest.mark.integration
def test_invalid_second_generation_preserves_current_and_auditable_budget(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    valid = service.generate(actor, actor.user_id, request())
    provider.invalid = True
    failed = service.generate(actor, actor.user_id, request())
    assert failed.estado == "SCHEMA_INVALIDO" and failed.versao_publicada_id is None
    assert (
        len(provider.calls) == 4
        and sum(c.chamadas_fisicas for c in failed.consumo) == 2
    )
    with sessions.begin() as session:
        current = published_workout(session, actor, actor.user_id)
        assert current and current.ficha.id == valid.versao_publicada_id


@pytest.mark.integration
def test_cancel_during_network_keeps_reservation_and_never_publishes(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    req = request()

    def cancel() -> None:
        service.cancel(actor, req.solicitacao_id)

    provider.hook = cancel
    result = service.generate(actor, actor.user_id, req)
    assert result.estado == "CANCELADA" and not result.versao_publicada_id
    assert result.consumo[0].chamadas_fisicas == 1 and result.consumo[0].uso
    assert service.generate(actor, actor.user_id, req).estado == "CANCELADA"
    assert len(provider.calls) == 1


@pytest.mark.integration
def test_equipment_change_before_delivery_prevents_publication(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    from app.modules.equipment.models import Equipment

    people, service, provider = scenario
    actor = people["cliente"]

    def change() -> None:
        if len(provider.calls) == 2:
            with sessions.begin() as session:
                item = session.scalar(select(Equipment))
                assert item is not None
                item.operacional = False
                item.revision += 1

    provider.hook = change
    result = service.generate(actor, actor.user_id, request())
    assert result.estado == "INTERROMPIDA" and not result.versao_publicada_id


@pytest.mark.integration
def test_retention_never_copies_expired_plan_into_execution(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    first = service.generate(actor, actor.user_id, request())
    for _ in range(15):
        assert service.generate(actor, actor.user_id, request()).estado == "PUBLICADA"
    with sessions.begin() as session:
        count = session.scalar(
            select(func.count())
            .select_from(WorkoutVersion)
            .where(WorkoutVersion.conteudo_excluido_em.is_(None))
        )
        assert count == 15
        expired = published_workout(
            session, actor, actor.user_id, first.versao_publicada_id
        )
        assert expired and not expired.ficha.dias and expired.ficha.explicacao is None
        assert all(
            "proposta" not in row.resultado
            for row in session.scalars(select(Execution))
        )


@pytest.mark.integration
def test_restart_or_deadline_never_resumes_physical_calls(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    people, service, provider = scenario
    actor = people["cliente"]
    req = request()
    state = PostgresState(sessions)
    from tests.ai.test_execution import setup

    _, contexts, _, _ = setup()
    from app.modules.ai.schemas.execution import RunResult

    initial = RunResult(
        solicitacao_id=req.solicitacao_id,
        estado="EM_EXECUCAO",
        motivo="INICIADA",
        modelo=Config.load().model,
        versao_prompts="v1",
        configuracao_sha256="a" * 64,
    )
    import time

    assert state.claim(
        actor, actor.user_id, req, "a" * 64, initial, time.perf_counter() + 100
    )[0]
    recovered = PostgresState(sessions, worker=uuid4()).lookup(
        actor, actor.user_id, req
    )
    assert recovered and recovered.estado == "INTERROMPIDA"
    assert (
        service.generate(actor, actor.user_id, req).estado == "INTERROMPIDA"
        and not provider.calls
    )


@pytest.mark.integration
def test_migration_roundtrip_and_metadata(
    migration: tuple[Connection, AlembicConfig],
) -> None:
    connection, config = migration
    command.upgrade(config, "head")
    context = MigrationContext.configure(
        connection,
        opts={
            "include_schemas": True,
            "include_name": lambda name, kind, parents: (
                kind != "schema" or name == "academia"
            ),
        },
    )
    assert not compare_metadata(context, Base.metadata)
    command.downgrade(config, "0013")
    command.upgrade(config, "head")
    assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0014"


@pytest.mark.integration
def test_retention_of_raw_execution_data_preserves_idempotency_and_counters(
    sessions: sessionmaker[Session], scenario: Scenario
) -> None:
    from datetime import timedelta

    from app.modules.ai.persistence.maintenance import purge_expired
    from app.modules.identity.service import utc_now

    people, service, provider = scenario
    actor = people["cliente"]
    req = request()
    original = service.generate(actor, actor.user_id, req)
    with sessions.begin() as session:
        row = session.scalar(select(Execution))
        assert row is not None
        row.iniciada_em -= timedelta(days=91)
        row.prazo_em -= timedelta(days=91)
        row.terminada_em = utc_now() - timedelta(days=91)
    assert purge_expired(sessions) == 1
    replay = service.generate(actor, actor.user_id, req)
    assert (
        replay.triagem is None
        and replay.versao_publicada_id == original.versao_publicada_id
    )
    assert len(replay.consumo) == 2 and len(provider.calls) == 2
    with sessions.begin() as session:
        triage = session.scalar(select(TriageRecord))
        assert triage is not None and triage.resumo == {}


@pytest.mark.integration
@pytest.mark.parametrize("change", ["fonte", "onboarding"])
def test_final_sql_guard_refuses_changed_source_or_snapshot(
    sessions: sessionmaker[Session],
    scenario: Scenario,
    change: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.ai.ports.execution import Context
    from app.modules.ai.schemas.execution import RunResult
    from app.modules.knowledge.models import DocumentVersion
    from app.modules.onboarding.schemas import ConfirmUpdate, OnboardingData
    from app.modules.onboarding.service import confirm_update, get_current_snapshot
    from tests.ai.test_triage import BASE

    people, service, provider = scenario
    actor = people["cliente"]
    original = service._publisher

    def guarded(
        context: Context,
    ) -> Callable[[Session, Actor, Execution, RunResult], UUID]:
        target = original(context)

        def publish(
            session: Session, actor: Actor, row: Execution, result: RunResult
        ) -> UUID:
            if change == "fonte":
                source = session.get(
                    DocumentVersion, result.evidencias[0].documento_versao_id
                )
                assert source is not None
                from app.modules.identity.service import utc_now

                source.estado = "REVOGADO"
                source.revogado_por = people["admin"].user_id
                source.revogado_em = utc_now()
                source.motivo_revogacao = "Teste de alteração final"
                source.revision += 1
            else:
                current = get_current_snapshot(session, actor.user_id)
                assert current is not None
                confirm_update(
                    session,
                    actor.user_id,
                    actor.user_id,
                    ConfirmUpdate(
                        versao_base=current.id,
                        confirmado=True,
                        dados=OnboardingData.model_validate(
                            {**BASE, "observacoes": "Nova informação confirmada"}
                        ),
                    ),
                )
            session.flush()
            return target(session, actor, row, result)

        return publish

    monkeypatch.setattr(service, "_publisher", guarded)
    result = service.generate(actor, actor.user_id, request())
    assert result.estado == "INTERROMPIDA" and not result.versao_publicada_id
    with sessions.begin() as session:
        assert session.scalar(select(func.count()).select_from(WorkoutVersion)) == 0
    assert len(provider.calls) == 2


@pytest.mark.integration
@pytest.mark.parametrize("blocked", [True, False])
def test_persistent_service_blocks_grave_or_unknown_before_network(
    sessions: sessionmaker[Session], scenario: Scenario, blocked: bool
) -> None:
    from app.modules.onboarding.schemas import ConfirmUpdate, OnboardingData
    from app.modules.onboarding.service import confirm_update, get_current_snapshot
    from tests.ai.test_triage import BASE

    people, service, provider = scenario
    actor = people["cliente"]
    data = {**BASE, "restricao_exercicio_declarada": "SIM" if blocked else "NAO_SEI"}
    with sessions.begin() as session:
        current = get_current_snapshot(session, actor.user_id)
        assert current is not None
        confirm_update(
            session,
            actor.user_id,
            actor.user_id,
            ConfirmUpdate(
                versao_base=current.id,
                confirmado=True,
                dados=OnboardingData.model_validate(data),
            ),
        )
    result = service.generate(actor, actor.user_id, request())
    assert result.estado == ("BLOQUEADA" if blocked else "DADOS_INSUFICIENTES")
    assert not provider.calls and not result.versao_publicada_id

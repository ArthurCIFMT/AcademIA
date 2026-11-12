"""Fixtures sintéticas exclusivas do E2E; nenhuma chamada ao LLM externo."""

import copy
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.evidence import RagEvidence
from app.modules.ai.generation import GenerationService
from app.modules.ai.ports.execution import Context, ProviderError
from app.modules.ai.schemas.execution import Completion, Stage
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.identity.accounts import create_account
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.knowledge.ingestion.indexing import Indexer
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.retrieval.contracts import Result, Scope
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Decision, Metadata, Purpose
from app.modules.knowledge.service import (
    approved_references,
    decide,
    is_approved,
    register,
)
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from app.modules.onboarding.schemas import Completion as FinishOnboarding
from app.modules.onboarding.schemas import DraftChange, DraftData
from app.modules.onboarding.service import complete_draft, save_draft
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.modules.training.catalog import create_exercise
from app.modules.training.schemas import ExerciseFields
from app.policies.access import Actor
from tests.ai.test_triage import BASE
from tests.knowledge.test_indexing import synthetic
from tests.knowledge.test_retrieval import QueryDouble


def seed_people(
    sessions: sessionmaker[Session], password: str, suffix: str
) -> tuple[dict[str, Actor], dict[str, Any]]:
    passwords = Passwords()
    email = f"e2e-admin-{suffix}@example.test"
    with sessions.begin() as session:

        def bootstrap() -> UUID:
            return bootstrap_admin(
                session,
                email=email,
                name="Administrador E2E",
                hired_on=date(2026, 1, 1),
                password=password,
                passwords=passwords,
                now=utc_now(),
            )

        admin = bootstrap()
        assert bootstrap() == admin
    people = {"admin": Actor(admin, frozenset({Role.ADMINISTRADOR}))}
    users: dict[str, Any] = {"admin": {"id": str(admin), "email": email}}
    roles = {
        "instrutor": Role.INSTRUTOR,
        "instrutor_alheio": Role.INSTRUTOR,
        "atendente": Role.ATENDENTE,
    }
    clients = [
        "seguranca",
        "adaptacao",
        "retencao",
        "equipamentos",
        "manual",
        "sem_instrutor",
        "sem_onboarding",
        "nao_sei",
        "grave",
    ]
    roles.update({name: Role.CLIENTE for name in clients})
    hashed = passwords.hash(password)
    with sessions.begin() as session:
        for name, role in roles.items():
            address = f"e2e-{name}-{suffix}@example.test"
            id = create_account(
                session,
                address,
                state=AccountState.ATIVO,
                password_hash=hashed,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=id, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=id,
                        nome=f"Cliente {name}",
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
            users[name] = {"id": str(id), "email": address}
        session.flush()
    for name in clients:
        if name == "sem_onboarding":
            continue
        data = copy.deepcopy(BASE)
        if name == "nao_sei":
            data["possui_condicoes_saude"] = "NAO_SEI"
        if name == "grave":
            data["possui_condicoes_saude"] = "SIM"
            data["condicoes_saude"] = [
                {
                    "categoria": "CARDIACA",
                    "descricao": "Condição grave sintética",
                    "gravidade_declarada": "GRAVE",
                }
            ]
        with sessions.begin() as session:
            actor = people[name]
            draft = save_draft(
                session,
                actor.user_id,
                actor.user_id,
                DraftChange(
                    versao_base=None, revisao=None, dados=DraftData.model_validate(data)
                ),
            )
            snapshot = complete_draft(
                session,
                actor.user_id,
                actor.user_id,
                FinishOnboarding(versao_base=None, revisao=draft.revisao),
            )
            users[name]["onboarding_id"] = str(snapshot.id)
            if name != "sem_instrutor":
                change_assignment(
                    session,
                    actor.user_id,
                    ChangeAssignment(
                        instrutor_id=people["instrutor"].user_id, vigente_id=None
                    ),
                    people["admin"],
                    uuid4(),
                )
    with sessions.begin() as session:
        exercise = create_exercise(
            session,
            ExerciseFields(
                nome="Agachamento E2E",
                descricao="Fixture sintética sem carga adicional.",
                grupo_muscular="Membros inferiores",
                ativo=True,
                dispensa_equipamento=True,
                combinacoes=[],
            ),
            admin,
            uuid4(),
        )
        users["exercicio"] = {"id": str(exercise.id)}
    return people, users


class BrowserModel:
    """JSON controlado testa integração/renderização, nunca qualidade do modelo."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(
        self,
        messages: list[dict[str, str]],
        stage: Stage,
        output_tokens: int,
        timeout: float,
        on_dispatch: Callable[[], None],
    ) -> Completion:
        on_dispatch()
        self.calls.append(stage)
        payload = json.loads(messages[1]["content"])["dados_nao_confiaveis"]
        refs = [payload["evidencias"][0]["fragmento_id"]]
        result: dict[str, Any]
        if stage == "TRIAGEM":
            result = {
                "alerta_grave": False,
                "lacuna": False,
                "atualizacao_onboarding_necessaria": False,
            }
        elif stage == "CHAT":
            text = json.dumps(payload, ensure_ascii=False)
            if "E2E_FALHA_LLM" in text:
                raise ProviderError("PROVEDOR_INDISPONIVEL")
            answer = "Resposta sintética de teste: cadência é o tempo de uma repetição."
            if "E2E_RENDERIZACAO" in text:
                answer = (
                    "<script>window.__e2eExecutou=true</script> "
                    '<img src="/e2e-ataque" onerror="window.__e2eExecutou=true"> '
                    '<a href="javascript:alert(1)">E2E_MARCADOR_PRIVADO</a>'
                )
            result = {
                "idioma": "pt-BR",
                "tipo": "INFORMACAO",
                "texto": answer,
                "evidencias_ids": refs,
            }
        elif payload.get("ficha_base"):
            result = copy.deepcopy(payload["ficha_base"])
            result.update(
                idioma="pt-BR",
                explicacao="Adaptação sintética de interface.",
                evidencias_ids=refs,
            )
            result["dias"][payload["dia_alvo"] - 1]["itens"][0]["series"] += 1
        else:
            candidate = payload["candidatos"][0]
            item = {
                "exercicio_id": candidate["id"],
                "equipamento_ids": candidate["combinacoes_disponiveis"][0],
                "ordem": 1,
                "series": 2,
                "repeticoes": "8-12",
                "carga_kg": None,
                "cadencia": None,
                "intervalo_segundos": 60,
                "observacoes": "Fixture E2E.",
            }
            result = {
                "idioma": "pt-BR",
                "dias": [
                    {"titulo": "Dia 1", "itens": [item]},
                    {"titulo": "Dia 2", "itens": [copy.deepcopy(item)]},
                ],
                "explicacao": "Ficha sintética; sem avaliação clínica.",
                "evidencias_ids": refs,
            }
        return Completion(content=json.dumps(result))


class BrowserEvidence:
    def __init__(self, port: RagEvidence, offline: UUID) -> None:
        self.port, self.offline = port, offline
        self.calls: list[str] = []

    def retrieve(
        self, context: Context, purpose: Purpose, query: str, scope: Scope | None = None
    ) -> Result:
        self.calls.append(str(context.client_id))
        if context.client_id == self.offline:
            raise ProviderError("PROVEDOR_INDISPONIVEL")
        return self.port.retrieve(context, purpose, query, scope)

    def current(self, evidences: tuple[Any, ...]) -> bool:
        return self.port.current(evidences)


class BrowserAI:
    def __init__(
        self, sessions: sessionmaker[Session], actor: Actor, offline: UUID, root: Path
    ) -> None:
        self.sessions = sessions
        self.model = BrowserModel()
        storage, ref, _, selection = synthetic(
            root,
            text=(
                "Fixture E2E sem validade científica. "
                "Cadência é o tempo de uma repetição. "
                "Não usar este texto como literatura para clientes reais."
            ),
        )
        metadata = Metadata.model_validate(
            {
                **ref.metadata.model_dump(),
                "finalidades": ["DUVIDAS", "TRIAGEM", "GERACAO_GERAL"],
            }
        )
        with sessions.begin() as session:
            version, _ = register(
                session,
                actor,
                "E2E-FIXTURE",
                "LITERATURA",
                metadata,
                "TXT",
                len(storage.read(ref.reference, ref.sha256)),
                ref.reference,
                ref.sha256,
                uuid4(),
            )
            decide(
                session,
                actor,
                version.id,
                Decision(revisao=1, estado="APROVADO"),
                storage,
                uuid4(),
            )
            approved = approved_references(session)[0]

        def approved_now(id: UUID, revision: int) -> bool:
            with sessions.begin() as session:
                return is_approved(session, id, revision)

        extraction = Extractor(storage, root=root / "extracao", parser=parse).extract(
            approved, approval_check=approved_now
        )
        self.encoder = QueryDouble()
        self.store = QdrantStore(VectorSettings(path=str(root / "qdrant")))
        for purpose in ("DUVIDAS", "TRIAGEM", "GERACAO_GERAL"):
            Indexer(sessions, self.store, self.encoder, lock_root=root / "locks").run(
                actor, extraction, selection.model_copy(update={"finalidade": purpose})
            )
        self.evidence = BrowserEvidence(
            RagEvidence(
                Retriever(sessions, self.store, self.encoder),
                sessions,
                self.store.check,
            ),
            offline,
        )

    def generator(
        self, sessions: sessionmaker[Session], **kwargs: Any
    ) -> GenerationService:
        return GenerationService(
            sessions, llm=self.model, evidence=self.evidence, **kwargs
        )

    def close(self) -> None:
        self.store.close()

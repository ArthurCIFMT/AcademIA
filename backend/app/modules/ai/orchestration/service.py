import json
import time
from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from pydantic import ValidationError

from app.contracts.structured import digest
from app.modules.ai.orchestration.presentation import present_plan
from app.modules.ai.orchestration.queries import (
    generation_evidence,
    generation_query,
    recovery_query,
)
from app.modules.ai.orchestration.settings import Config
from app.modules.ai.orchestration.validation import validate_chat, validate_plan
from app.modules.ai.policies.triage import Policy
from app.modules.ai.ports.execution import (
    ContextPort,
    EvidencePort,
    LLMPort,
    ProviderError,
    StatePort,
)
from app.modules.ai.prompts.v1 import VERSION, build
from app.modules.ai.schemas.execution import (
    ChatAnswer,
    Consumption,
    PlanAnswer,
    RunRequest,
    RunResult,
    Stage,
    TriageAnswer,
)
from app.modules.ai.schemas.parsing import parse_object
from app.modules.ai.triage.contracts import Signals, SummaryData
from app.modules.ai.triage.engine import Engine
from app.modules.knowledge.retrieval.contracts import Evidence
from app.modules.knowledge.schemas import Purpose
from app.policies.access import Actor

Answer = TypeVar("Answer", TriageAnswer, ChatAnswer, PlanAnswer)


class Stop(Exception):
    def __init__(self, state: str, code: str) -> None:
        self.state, self.code = state, code
        super().__init__(code)


class Orchestrator:
    def __init__(
        self,
        contexts: ContextPort,
        evidence: EvidencePort,
        llm: LLMPort,
        state: StatePort,
        *,
        config: Config | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.contexts, self.evidence, self.llm, self.state = (
            contexts,
            evidence,
            llm,
            state,
        )
        self.config, self.clock = config or Config.load(), clock

    def execute(self, actor: Actor, client_id: UUID, request: RunRequest) -> RunResult:
        started = self.clock()
        deadline = started + self.config.deadline_seconds
        context = self.contexts.resolve(actor, client_id, request)
        if context.actor_id != actor.user_id or context.client_id != client_id:
            raise ValueError("Contexto não corresponde ao ator/titular autorizado.")
        initial = RunResult(
            solicitacao_id=request.solicitacao_id,
            estado="EM_EXECUCAO",
            motivo="INICIADA",
            modelo=self.config.model,
            versao_prompts=VERSION,
            configuracao_sha256=self.config.fingerprint,
        )
        created, previous = self.state.claim(
            actor,
            client_id,
            request,
            digest(
                {
                    "request": request.model_dump(mode="json"),
                    "context": context.fingerprint,
                    "config": self.config.fingerprint,
                    "prompts": VERSION,
                }
            ),
            initial,
            deadline,
        )
        if not created:
            if previous.evidencias and not self.evidence.current(
                tuple(previous.evidencias)
            ):
                return previous.model_copy(
                    update={
                        "estado": "ABSTENCAO",
                        "motivo": "EVIDENCIA_SUPERADA",
                        "resposta": None,
                        "proposta": None,
                    }
                )
            return previous
        result = initial
        gathered: dict[UUID, Evidence] = {}
        phases: list[str] = []

        def phase(name: str) -> None:
            phases.append(name)
            self.state.phase(actor, request.solicitacao_id, name)

        def active() -> None:
            if self.clock() >= deadline:
                raise Stop("TIMEOUT", "ORCAMENTO_EXCEDIDO")
            if not self.state.active(actor, request.solicitacao_id, self.clock()):
                raise Stop("CANCELADA", "EXECUCAO_ENCERRADA")
            if not self.contexts.current(actor, context, request):
                raise Stop("INTERROMPIDA", "CONTEXTO_SUPERADO")
            if gathered and not self.evidence.current(tuple(gathered.values())):
                raise Stop("ABSTENCAO", "EVIDENCIA_SUPERADA")

        def retrieve(
            purpose: Purpose, query: str, *, health: bool = False
        ) -> tuple[Evidence, ...]:
            active()
            if not query.strip() or len(query) > 1000:
                raise Stop("LIMITE_EXCEDIDO", "CONSULTA_EXCEDE_CONTEXTO")
            package = self.evidence.retrieve(
                context, purpose, query, context.health_scope if health else None
            )
            if package.estado == "CONFLITO":
                raise Stop("CONFLITO", "FONTES_CONFLITANTES")
            if package.estado == "SERVICO_INDISPONIVEL":
                raise Stop("FALHA", "RAG_INDISPONIVEL")
            if package.estado != "EVIDENCIAS_ENCONTRADAS" or not package.evidencias:
                raise Stop("ABSTENCAO", "EVIDENCIA_INSUFICIENTE")
            if len(package.evidencias) > 5:
                raise Stop("LIMITE_EXCEDIDO", "PACOTE_EXCEDE_CONTEXTO")
            if health and (
                context.health_scope is None or package.suporte_saude != "PERTINENTE"
            ):
                raise Stop("ABSTENCAO", "SUPORTE_SAUDE_INSUFICIENTE")
            for e in package.evidencias:
                gathered[e.fragmento_id] = e
            active()
            return tuple(package.evidencias)

        def call(
            stage: Stage, payload: dict[str, object], expected: type[Answer]
        ) -> Answer:
            active()
            try:
                messages = build(stage, payload, self.config.prompt_bytes)
            except ValueError:
                raise Stop("LIMITE_EXCEDIDO", "CONTEXTO_EXCEDIDO") from None
            tokens, timeout = self.config.stage_limits(stage)
            self.state.reserve(
                actor,
                request.solicitacao_id,
                Consumption(
                    etapa=stage,
                    chamadas_fisicas=0,
                    limite_saida_tokens=tokens,
                    prompt_bytes=len(
                        json.dumps(
                            messages, ensure_ascii=False, separators=(",", ":")
                        ).encode()
                    ),
                    prompt_sha256=digest(messages),
                ),
            )
            active()
            dispatched = False

            def dispatch() -> None:
                nonlocal dispatched
                active()
                if dispatched:
                    raise Stop("LIMITE_EXCEDIDO", "TENTATIVA_REPETIDA")
                self.state.dispatched(actor, request.solicitacao_id, stage)
                dispatched = True

            completion = self.llm.complete(
                messages, stage, tokens, min(timeout, deadline - self.clock()), dispatch
            )
            if not dispatched:
                raise Stop("FALHA", "ADAPTADOR_SEM_REGISTRO_DE_CHAMADA")
            self.state.usage(actor, request.solicitacao_id, stage, completion)
            active()
            try:
                parsed = parse_object(completion.content)
            except (ValueError, TypeError):
                raise Stop("JSON_INVALIDO", "JSON_INVALIDO") from None
            try:
                return expected.model_validate(parsed)
            except ValidationError:
                raise Stop("SCHEMA_INVALIDO", "SAIDA_FORA_DO_SCHEMA") from None

        try:
            active()
            if request.finalidade == "DUVIDA":
                phase("BUSCA_DUVIDA")
                evidence = retrieve("DUVIDAS", request.mensagem)
                phase("RESPOSTA")
                answer = call(
                    "CHAT",
                    {
                        "pergunta": request.mensagem,
                        "historico": [
                            m.model_dump(mode="json") for m in request.historico
                        ],
                        "evidencias": [e.model_dump(mode="json") for e in evidence],
                    },
                    ChatAnswer,
                )
                assert isinstance(answer, ChatAnswer)
                phase("VALIDACAO")
                validate_chat(answer, evidence)
                result = result.model_copy(
                    update={
                        "estado": "ABSTENCAO"
                        if answer.tipo == "ABSTENCAO"
                        else "RESPOSTA_PRONTA",
                        "motivo": "RESPOSTA_VALIDADA",
                        "resposta": answer,
                    }
                )
            else:
                phase("TRIAGEM")
                prep = context.preparation
                if prep is None:
                    raise Stop("DADOS_INSUFICIENTES", "SEM_ONBOARDING_VALIDO")
                result = result.model_copy(update={"triagem": prep})
                if prep.estado in {"BLOQUEADO_POR_SEGURANCA", "DADOS_INSUFICIENTES"}:
                    raise Stop(
                        "BLOQUEADA"
                        if prep.estado == "BLOQUEADO_POR_SEGURANCA"
                        else "DADOS_INSUFICIENTES",
                        prep.motivos[0],
                    )
                if prep.resumo is None:
                    raise Stop("DADOS_INSUFICIENTES", "RESUMO_INDISPONIVEL")
                if not context.candidates:
                    raise Stop("ABSTENCAO", "SEM_EXERCICIOS_VIAVEIS")
                if len(context.candidates) > 40:
                    raise Stop("LIMITE_EXCEDIDO", "CATALOGO_EXCEDE_CONTEXTO")
                if request.finalidade == "ADAPTACAO" and (
                    context.base_plan is None
                    or context.base_version_id != request.versao_base_id
                ):
                    raise Stop("DADOS_INSUFICIENTES", "BASE_ADAPTACAO_AUSENTE")
                summary = prep.resumo.conteudo
                health_query = json.dumps(
                    {
                        "condicoes": [
                            c.model_dump(mode="json")
                            for c in summary.dados.condicoes_saude
                        ],
                        "limitacoes": [
                            item.model_dump(mode="json")
                            for item in summary.dados.limitacoes
                        ],
                        "medicacoes": [
                            item.model_dump(mode="json")
                            for item in summary.dados.medicamentos
                        ],
                        "observacoes": summary.dados.observacoes,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                triage_evidence = retrieve(
                    "TRIAGEM",
                    "Cuidados e restrições para atividade física: " + health_query,
                )
                parent = self

                class Analyst:
                    def analyze(
                        self,
                        content: SummaryData,
                        evidences: tuple[Evidence, ...],
                        policy: Policy,
                    ) -> Signals:
                        analyzed = call(
                            "TRIAGEM",
                            {
                                "resumo": content.model_dump(mode="json"),
                                "solicitacao": request.mensagem,
                                "politica": policy.model_dump(mode="json"),
                                "evidencias": [
                                    e.model_dump(mode="json") for e in evidences
                                ],
                            },
                            TriageAnswer,
                        )
                        assert isinstance(analyzed, TriageAnswer)
                        if analyzed.atualizacao_onboarding_necessaria:
                            analyzed = analyzed.model_copy(update={"lacuna": True})
                        return Signals.model_validate(
                            analyzed.model_dump(
                                exclude={"atualizacao_onboarding_necessaria"}
                            )
                        )

                analyzed = Engine(Analyst(), clock=parent.clock).evaluate(
                    snapshot=prep.snapshot,
                    completed=True,
                    age=summary.idade,
                    data=summary.dados,
                    candidates=len(context.candidates),
                    resources_hash=prep.recursos_sha256,
                    evidences=triage_evidence,
                )
                result = result.model_copy(update={"triagem": analyzed})
                if analyzed.estado != "ELEGIVEL_PARA_GERACAO":
                    raise Stop(
                        "BLOQUEADA"
                        if analyzed.estado == "BLOQUEADO_POR_SEGURANCA"
                        else "TIMEOUT"
                        if analyzed.estado_tecnico == "TIMEOUT"
                        else "DADOS_INSUFICIENTES"
                        if analyzed.estado == "DADOS_INSUFICIENTES"
                        else "FALHA",
                        analyzed.motivos[0],
                    )
                phase("BUSCA_GERACAO")
                health = (
                    summary.dados.possui_condicoes_saude == "SIM"
                    or summary.dados.possui_dor_lesao_limitacao == "SIM"
                    or summary.dados.usa_medicamentos == "SIM"
                )
                evidence = retrieve(
                    "GERACAO_GERAL",
                    generation_query(summary, health_query),
                    health=health,
                )
                recovery = retrieve(
                    "GERACAO_GERAL",
                    recovery_query(summary, health_query),
                    health=health,
                )
                evidence = generation_evidence(evidence, recovery)
                phase("GERACAO")
                plan = call(
                    "GERACAO",
                    {
                        "resumo": summary.model_dump(mode="json"),
                        "solicitacao": request.mensagem,
                        "dia_alvo": request.dia_alvo,
                        "candidatos": [
                            c.model_dump(mode="json") for c in context.candidates
                        ],
                        "exercicios_proibidos": [
                            str(x) for x in sorted(context.forbidden_ids)
                        ],
                        "evidencias": [e.model_dump(mode="json") for e in evidence],
                        "ficha_base": context.base_plan.model_dump(mode="json")
                        if context.base_plan
                        else None,
                    },
                    PlanAnswer,
                )
                assert isinstance(plan, PlanAnswer)
                phase("VALIDACAO")
                validate_plan(plan, context, evidence)
                if request.finalidade == "ADAPTACAO":
                    if (
                        not context.base_plan
                        or not request.dia_alvo
                        or request.dia_alvo > len(context.base_plan.dias)
                        or len(plan.dias) != len(context.base_plan.dias)
                    ):
                        raise ValueError("DIFF_INVALIDO")
                    if (
                        context.base_plan.dias[request.dia_alvo - 1]
                        == plan.dias[request.dia_alvo - 1]
                    ):
                        raise Stop("ABSTENCAO", "SEM_ALTERACOES")
                    for index, old in enumerate(context.base_plan.dias, 1):
                        if index != request.dia_alvo and old != plan.dias[index - 1]:
                            raise ValueError("ALTERACAO_FORA_DO_DIA_ALVO")
                plan = present_plan(plan, adaptation=request.finalidade == "ADAPTACAO")
                result = result.model_copy(
                    update={
                        "estado": "PRONTA_PARA_PUBLICACAO",
                        "motivo": "PROPOSTA_VALIDADA",
                        "proposta": plan,
                    }
                )
            active()
            phase("FINALIZADA")
        except Stop as stopped:
            result = RunResult.model_validate(
                {
                    **result.model_dump(mode="json"),
                    "estado": stopped.state,
                    "motivo": stopped.code,
                    "proposta": None,
                    "resposta": None,
                }
            )
        except ProviderError as error:
            result = result.model_copy(
                update={
                    "estado": "TIMEOUT" if error.code == "TIMEOUT" else "FALHA",
                    "motivo": error.code,
                    "proposta": None,
                    "resposta": None,
                }
            )
        except (ValueError, ValidationError):
            result = result.model_copy(
                update={
                    "estado": "SCHEMA_INVALIDO",
                    "motivo": "RESTRICAO_OU_CONTRATO_INVALIDO",
                    "proposta": None,
                    "resposta": None,
                }
            )
        result = result.model_copy(
            update={"etapas": phases, "evidencias": list(gathered.values())}
        )
        return self.state.finish(actor, request.solicitacao_id, result)

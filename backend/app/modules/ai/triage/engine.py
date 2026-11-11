import hashlib
import json
import time
from collections.abc import Callable
from uuid import UUID

from pydantic import ValidationError

from app.modules.ai.policies.triage import Policy
from app.modules.ai.triage.contracts import (
    AnalysisUnavailable,
    Analyst,
    DomainState,
    Reason,
    Signals,
    SnapshotRef,
    Summary,
    SummaryData,
    TechnicalState,
    TriageResult,
)
from app.modules.knowledge.retrieval.contracts import Evidence
from app.modules.onboarding.schemas import Condition, Limitation, OnboardingData


class Engine:
    def __init__(
        self,
        analyst: Analyst | None = None,
        *,
        policy: Policy | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.analyst, self.policy, self.clock = analyst, policy or Policy(), clock

    def evaluate(
        self,
        *,
        snapshot: SnapshotRef | None,
        completed: bool,
        age: object,
        data: object,
        candidates: int = 0,
        resources_hash: str | None = None,
        evidences: tuple[Evidence, ...] = (),
    ) -> TriageResult:
        summary: Summary | None = None
        used: list[UUID] = []

        def result(
            state: DomainState | None,
            code: Reason,
            technical: TechnicalState = "CONCLUIDA",
        ) -> TriageResult:
            reasons: list[Reason] = [code]
            allowed = (
                state == "ELEGIVEL_PARA_GERACAO"
                and technical == "CONCLUIDA"
                and candidates > 0
            )
            if state == "ELEGIVEL_PARA_GERACAO" and candidates == 0:
                reasons.append("SEM_EXERCICIOS_VIAVEIS")
            return TriageResult(
                snapshot=snapshot,
                regra_versao=self.policy.version,
                regra_sha256=self.policy.fingerprint,
                estado=state,
                estado_tecnico=technical,
                motivos=reasons,
                resumo_sha256=summary.sha256 if summary else None,
                evidencias_ids=used,
                exercicios_elegiveis=candidates,
                recursos_sha256=resources_hash,
                geracao_permitida=allowed,
                resumo=summary,
            )

        if not completed or snapshot is None:
            return result("DADOS_INSUFICIENTES", "ONBOARDING_NAO_CONCLUIDO")
        try:
            parsed = OnboardingData.model_validate(data)
        except ValidationError:
            return result("DADOS_INSUFICIENTES", "DADOS_INVALIDOS")
        if type(age) is not int or age < 0:
            return result("DADOS_INSUFICIENTES", "IDADE_AUSENTE")
        content = SummaryData(idade=age, dados=parsed)
        raw = json.dumps(
            content.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")
        )
        if len(raw) <= self.policy.max_summary_chars:
            summary = Summary(
                conteudo=content,
                caracteres=len(raw),
                sha256=hashlib.sha256(raw.encode()).hexdigest(),
            )
        if age < self.policy.minimum_age:
            return result("BLOQUEADO_POR_SEGURANCA", "ESCOPO_ETARIO")
        occurrences: list[Condition | Limitation] = [
            *parsed.condicoes_saude,
            *parsed.limitacoes,
        ]
        if (
            any(item.gravidade_declarada == "GRAVE" for item in occurrences)
            or parsed.restricao_exercicio_declarada == "SIM"
            or parsed.evento_saude_importante_recente == "SIM"
        ):
            return result("BLOQUEADO_POR_SEGURANCA", "ALERTA_GRAVE_DECLARADO")
        flags = [
            parsed.possui_condicoes_saude,
            parsed.usa_medicamentos,
            parsed.possui_dor_lesao_limitacao,
            parsed.restricao_exercicio_declarada,
            parsed.evento_saude_importante_recente,
        ]
        if "NAO_SEI" in flags or any(
            item.gravidade_declarada == "NAO_SEI" for item in occurrences
        ):
            return result("DADOS_INSUFICIENTES", "DADO_DESCONHECIDO")
        if summary is None:
            return result("DADOS_INSUFICIENTES", "CONTEXTO_EXCEDIDO")
        if self.analyst is None:
            return result(None, "ANALISE_PENDENTE", "AGUARDANDO_ANALISE")
        started = self.clock()
        try:
            # A porta recebe cópia sem IDs privados e não altera a projeção original.
            returned = self.analyst.analyze(
                content.model_copy(deep=True), evidences, self.policy
            )
            signals = Signals.model_validate(
                returned.model_dump() if isinstance(returned, Signals) else returned
            )
        except TimeoutError:
            return result(None, "TIMEOUT_ANALISE", "TIMEOUT")
        except AnalysisUnavailable:
            return result(None, "FALHA_ANALISE", "FALHA")
        except (ValidationError, ValueError, TypeError):
            return result(None, "SAIDA_ANALISE_INVALIDA", "FALHA")
        if self.clock() - started >= self.policy.analysis_timeout_seconds:
            return result(None, "TIMEOUT_ANALISE", "TIMEOUT")
        if not set(signals.evidencias_ids) <= {e.fragmento_id for e in evidences}:
            return result(None, "EVIDENCIA_NAO_FORNECIDA", "FALHA")
        used = list(dict.fromkeys(signals.evidencias_ids))
        if signals.alerta_grave:
            return result("BLOQUEADO_POR_SEGURANCA", "ALERTA_GRAVE_TEXTO")
        if signals.lacuna or signals.contradicao:
            return result("DADOS_INSUFICIENTES", "LACUNA_OU_CONTRADICAO")
        return result("ELEGIVEL_PARA_GERACAO", "ANALISE_CONCLUIDA")

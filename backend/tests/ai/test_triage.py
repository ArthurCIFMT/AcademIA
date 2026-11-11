import copy
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.modules.ai.policies.triage import Policy
from app.modules.ai.triage.contracts import (
    AnalysisUnavailable,
    Signals,
    SnapshotRef,
    SummaryData,
    TriageResult,
)
from app.modules.ai.triage.engine import Engine
from app.modules.knowledge.retrieval.contracts import Evidence

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "docs/testes/casos-triagem-v1.json").read_text("utf-8"))[
    "casos"
]
BASE = CASES[0]["entrada"]["dados"]


class Double:
    def __init__(
        self, signals: Signals | None = None, error: Exception | None = None
    ) -> None:
        self.signals = (
            signals
            if signals is not None
            else Signals(alerta_grave=False, lacuna=False)
        )
        self.error = error
        self.received: list[SummaryData] = []

    def analyze(
        self, summary: SummaryData, evidences: tuple[Evidence, ...], policy: Policy
    ) -> Signals:
        self.received.append(summary)
        if self.error:
            raise self.error
        return self.signals


def evaluate(
    engine: Engine, data: object = None, age: object = 30, completed: bool = True
) -> TriageResult:
    return engine.evaluate(
        snapshot=SnapshotRef(id=uuid4(), numero=1, revisao=2),
        completed=completed,
        age=age,
        data=copy.deepcopy(BASE if data is None else data),
        candidates=1,
        resources_hash="0" * 64,
    )


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c["id"] not in {"T16", "T18", "T21", "T22", "T23"}],
    ids=lambda c: c["id"],
)
def test_approved_decision_table(case: dict[str, object]) -> None:
    entry = case["entrada"]
    assert isinstance(entry, dict)
    signals = Signals.model_validate(
        entry.get("llm", {"alerta_grave": False, "lacuna": False})
    )
    error = (
        TimeoutError()
        if entry.get("erro_provedor") == "TIMEOUT"
        else AnalysisUnavailable()
        if entry.get("erro_provedor")
        else None
    )
    analyst = Double(signals, error)
    policy = Policy(max_summary_chars=1) if entry.get("contexto_excedido") else Policy()
    result = evaluate(
        Engine(analyst, policy=policy),
        data=entry.get("dados", {}),
        age=entry.get("idade"),
        completed=entry.get("onboarding_concluido", True),
    )
    expected = case["esperado"]
    if expected == "FALHA_TECNICA_SEM_TRIAGEM":
        assert result.estado is None and result.estado_tecnico in {"FALHA", "TIMEOUT"}
    else:
        assert result.estado == expected
    if expected != "ELEGIVEL_PARA_GERACAO":
        assert not result.geracao_permitida
    if case["id"] in {"T03", "T04", "T05", "T06", "T19", "T24"}:
        assert not analyst.received


def test_missing_analyzer_never_invents_eligibility() -> None:
    result = evaluate(Engine())
    assert result.estado is None and result.estado_tecnico == "AGUARDANDO_ANALISE"
    assert not result.geracao_permitida


def test_summary_preserves_fields_and_excludes_identity() -> None:
    data = copy.deepcopy(BASE)
    data.update(
        {
            "possui_condicoes_saude": "SIM",
            "condicoes_saude": [
                {
                    "categoria": "OUTRA",
                    "descricao": "Não presumir ausência de restrições.",
                    "gravidade_declarada": "NAO_GRAVE",
                }
            ],
            "usa_medicamentos": "SIM",
            "medicamentos": [
                {"nome": "medicamento sintético", "observacao": "Não alterar uso"}
            ],
            "observacoes": "Alerta sintético preservado",
        }
    )
    analyst = Double()
    result = evaluate(Engine(analyst), data=data)
    assert result.resumo is not None
    sent = analyst.received[0].model_dump(mode="json")
    assert sent["dados"] == data and sent["idade"] == 30
    assert set(sent) == {"idade", "dados"}
    assert "snapshot" not in sent and "cliente_id" not in sent
    assert result.snapshot is not None and result.resumo.sha256 == result.resumo_sha256


def test_real_size_overflow_does_not_truncate_or_call_analyzer() -> None:
    data = copy.deepcopy(BASE)
    data.update(
        {
            "usa_medicamentos": "SIM",
            "medicamentos": [
                {"nome": "Sintético", "observacao": "Não remover alerta. " * 15}
                for _ in range(8)
            ],
        }
    )
    analyst = Double()
    result = evaluate(Engine(analyst), data=data)
    assert result.estado == "DADOS_INSUFICIENTES" and result.resumo is None
    assert "CONTEXTO_EXCEDIDO" in result.motivos and not analyst.received


def test_severe_flag_wins_over_unknown_and_context_overflow() -> None:
    data = copy.deepcopy(BASE)
    data.update({"restricao_exercicio_declarada": "SIM", "usa_medicamentos": "NAO_SEI"})
    result = evaluate(Engine(Double(), policy=Policy(max_summary_chars=1)), data=data)
    assert result.estado == "BLOQUEADO_POR_SEGURANCA"
    assert result.motivos == ["ALERTA_GRAVE_DECLARADO"]


def test_invalid_assisted_output_and_invented_evidence_fail_closed() -> None:
    invalid = Signals(alerta_grave=False, lacuna=False).model_copy(
        update={"lacuna": None}
    )
    result = evaluate(Engine(Double(invalid)))
    assert result.estado is None and result.estado_tecnico == "FALHA"
    invented = Signals(alerta_grave=False, lacuna=False, evidencias_ids=[uuid4()])
    result = evaluate(Engine(Double(invented)))
    assert result.estado is None and result.motivos == ["EVIDENCIA_NAO_FORNECIDA"]


def test_late_output_does_not_become_eligible() -> None:
    ticks = iter([0.0, 26.0])
    result = evaluate(Engine(Double(), clock=lambda: next(ticks)))
    assert result.estado is None and result.estado_tecnico == "TIMEOUT"


def test_missing_age_bool_age_and_no_equipment_are_distinct() -> None:
    assert evaluate(Engine(Double()), age=None).estado == "DADOS_INSUFICIENTES"
    assert evaluate(Engine(Double()), age=True).estado == "DADOS_INSUFICIENTES"
    result = Engine(Double()).evaluate(
        snapshot=SnapshotRef(id=uuid4(), numero=1, revisao=2),
        completed=True,
        age=30,
        data=BASE,
        candidates=0,
    )
    assert result.estado == "ELEGIVEL_PARA_GERACAO" and not result.geracao_permitida
    assert "SEM_EXERCICIOS_VIAVEIS" in result.motivos

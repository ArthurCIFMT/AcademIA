from copy import deepcopy
from typing import Any

import pytest

from tests.acceptance.consolidation import REQUIRED, assess


def evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    browser = {
        "codigo_sha256": {"app": "current"},
        "casos": [
            {
                "id": f"E2E-{n:02}",
                "passou": True,
                "tentativas": 1,
                "estado": "expected",
                "navegador": "Edge",
            }
            for n in range(1, 9)
        ],
        "modo": "E2E_HTTP_REAL_IA_CONTROLADA",
        "testes_locais_aprovados": True,
        "codigo_navegador": 0,
        "bootstrap_idempotente": True,
        "rollback_confirmado": True,
        "persistencia": {"versoes": 1, "auditorias": 1, "avisos": 1},
        "migration": "0015",
        "chamadas_llm_externo": 0,
    }
    critical = {
        "modo": "REGRESSAO_CRITICA_LOCAL_SEM_LLM",
        "chamadas_llm_externo": 0,
        "codigo_sha256": {"app": "current"},
        "testes_sha256": {"test": "current"},
        "testes": [{"teste": s, "estado": "APROVADO"} for s in REQUIRED],
    }
    ai = {"estado": "APROVADO", "aceite_ia_real": True, "criterios": {"real": True}}
    return browser, critical, ai


def decide(
    browser: dict[str, Any],
    critical: dict[str, Any],
    ai: dict[str, Any],
    reproduced: bool = True,
) -> dict[str, Any]:
    return assess(
        browser,
        critical,
        ai,
        current={"app": "current"},
        sources={"test": "current"},
        migration="0015",
        ai_reproduced=reproduced,
    )


def test_complete_bound_evidence_closes_only_mvp() -> None:
    result = decide(*evidence())
    assert result["aceite_mvp"] and all(result["criterios"].values())
    assert result["marco"] == "PG-01"


@pytest.mark.parametrize(
    "fault",
    [
        "old_runtime",
        "old_critical",
        "missing_test",
        "duplicate_test",
        "failed_test",
        "missing_journey",
        "browser_retry",
        "rollback",
        "migration",
        "ai_hash",
        "ai_pending",
    ],
)
def test_missing_stale_failed_or_unbound_evidence_cannot_close_mvp(fault: str) -> None:
    browser, critical, ai = deepcopy(evidence())
    if fault == "old_runtime":
        browser["codigo_sha256"]["app"] = "old"
    elif fault == "old_critical":
        critical["testes_sha256"]["test"] = "old"
    elif fault == "missing_test":
        critical["testes"].pop()
    elif fault == "duplicate_test":
        critical["testes"][-1] = critical["testes"][0]
    elif fault == "failed_test":
        critical["testes"][0]["estado"] = "IGNORADO"
    elif fault == "missing_journey":
        browser["casos"].pop()
    elif fault == "browser_retry":
        browser["casos"][0]["tentativas"] = 2
    elif fault == "rollback":
        browser["rollback_confirmado"] = False
    elif fault == "migration":
        browser["migration"] = "0014"
    elif fault == "ai_pending":
        ai["aceite_ia_real"] = False
    assert not decide(browser, critical, ai, fault != "ai_hash")["aceite_mvp"]


def test_output_cannot_overwrite_previous_evidence(
    tmp_path: Any, monkeypatch: Any
) -> None:
    from tests.acceptance.consolidation.__main__ import main

    output = tmp_path / "receipt.json"
    output.write_text("preservar", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["consolidation", "--output", str(output)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert output.read_text("utf-8") == "preservar"

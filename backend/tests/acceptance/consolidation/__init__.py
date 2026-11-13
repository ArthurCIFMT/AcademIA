"""Aceite reproduzível: E2E existente + regressão crítica + AI-06 real."""

import json
from pathlib import Path
from typing import Any

from alembic.script import ScriptDirectory

from app.contracts.structured import digest
from tests.acceptance.__main__ import ROOT, local_acceptance, runtime_identity
from tests.ai.evaluation.consolidation import consolidate as consolidate_ai
from tests.ai.evaluation.reporting import json_sha, sha

REQUIRED = (
    "tests/ai/test_chat_concurrency.py::test_chat_concurrent_reservations_replay_and_shared_quota",
    "tests/ai/test_evaluation_guards.py::test_sixteenth_version_cannot_be_recovered_from_chat",
    "tests/ai/test_evaluation_guards.py::test_manual_workout_does_not_depend_on_any_ai_service",
    "tests/ai/test_followup.py::test_followup_sources_pending_notice_failure_and_idempotent_resend",
    "tests/ai/test_generation.py::test_equipment_change_before_delivery_prevents_publication",
    "tests/ai/test_generation.py::test_final_sql_guard_refuses_changed_source_or_snapshot[fonte]",
    "tests/ai/test_generation.py::test_final_sql_guard_refuses_changed_source_or_snapshot[onboarding]",
    "tests/ai/test_generation_concurrency.py::test_atomic_claim_dispatch_and_shared_rate_limit_in_independent_connections",
    "tests/knowledge/test_evaluation_attack.py::test_real_attack_fixture_reaches_retrieval_without_provider",
    "tests/onboarding/test_onboarding.py::test_reissue_revokes_unused_link_and_concurrent_exchange_consumes_once",
    "tests/training/test_catalog.py::test_publication_revalidates_snapshot_inventory_and_draft",
    "tests/training/test_catalog.py::test_concurrent_publication_and_rejection[publish]",
    "tests/training/test_catalog.py::test_concurrent_publication_and_rejection[replay]",
    "tests/training/test_catalog.py::test_concurrent_publication_and_rejection[reject]",
)


def critical_sources() -> dict[str, str]:
    import hashlib

    return {
        name: hashlib.sha256(
            (ROOT / "backend" / name).read_text("utf-8").replace("\r\n", "\n").encode()
        ).hexdigest()
        for name in sorted({s.split("::")[0] for s in REQUIRED})
    }


def assess(
    browser: dict[str, Any],
    critical: dict[str, Any],
    ai: dict[str, Any],
    *,
    current: dict[str, str],
    sources: dict[str, str],
    migration: str | None,
    ai_reproduced: bool,
) -> dict[str, Any]:
    rows = browser.get("casos", [])
    tests = critical.get("testes", [])
    ids = [r.get("teste") for r in tests]
    counts = browser.get("persistencia", {})
    criteria = {
        "e2e_mesmo_codigo": bool(current) and browser.get("codigo_sha256") == current,
        "oito_jornadas_uma_tentativa": local_acceptance(rows)
        and all(
            r.get("tentativas") == 1 and r.get("estado") == "expected" for r in rows
        ),
        "navegador_e_api_reais": browser.get("modo") == "E2E_HTTP_REAL_IA_CONTROLADA"
        and browser.get("testes_locais_aprovados") is True
        and browser.get("codigo_navegador") == 0
        and all(bool(r.get("navegador")) for r in rows),
        "bootstrap_persistencia_rollback": browser.get("bootstrap_idempotente") is True
        and browser.get("rollback_confirmado") is True
        and all(
            type(counts.get(k)) is int and counts[k] > 0
            for k in ("versoes", "auditorias", "avisos")
        ),
        "migration_atual": bool(migration) and browser.get("migration") == migration,
        "e2e_controlado_separado_do_modelo": browser.get("chamadas_llm_externo") == 0,
        "criticos_mesmo_codigo_e_fontes": critical.get("codigo_sha256") == current
        and critical.get("testes_sha256") == sources,
        "criticos_completos_aprovados": critical.get("modo")
        == "REGRESSAO_CRITICA_LOCAL_SEM_LLM"
        and critical.get("chamadas_llm_externo") == 0
        and len(ids) == len(REQUIRED)
        and set(ids) == set(REQUIRED)
        and all(r.get("estado") == "APROVADO" for r in tests),
        "ai06_real_aprovado_reproduzido": ai_reproduced
        and ai.get("estado") == "APROVADO"
        and ai.get("aceite_ia_real") is True
        and bool(ai.get("criterios"))
        and all(v is True for v in ai["criterios"].values()),
    }
    approved = all(criteria.values())
    return {
        "schema_version": 1,
        "estado": "APROVADO" if approved else "PENDENTE_OU_REPROVADO",
        "aceite_mvp": approved,
        "marco": "PG-01",
        "criterios": criteria,
        "codigo_atual_sha256": digest(current),
        "arquivos_runtime_verificados": len(current),
        "jornadas": len(rows),
        "criticos": len(tests),
        "nota": (
            "Aceite do MVP acadêmico. IA real é a amostra v4; "
            "não aprova módulos pós-MVP."
        ),
    }


def consolidate(browser_path: Path, critical_path: Path) -> dict[str, Any]:
    folder = ROOT / "docs/testes"

    def read(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text("utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("Relatório deve ser objeto JSON.")
        return value

    ai_path = folder / "ai06-consolidacao.json"
    ai = read(ai_path)
    reproduced = consolidate_ai(
        folder / "ai06-deterministico.json",
        folder / "ai06-ensaio-real.json",
        folder / "ai06-revisao-tecnica.json",
    )
    result = assess(
        read(browser_path),
        read(critical_path),
        ai,
        current=runtime_identity(),
        sources=critical_sources(),
        migration=ScriptDirectory(str(ROOT / "database/migrations")).get_current_head(),
        ai_reproduced=reproduced == ai,
    )
    result["algoritmo_hash"] = "JSON_CANONICO_V1"
    result["entradas_sha256"] = {
        "e2e": json_sha(browser_path),
        "criticos": json_sha(critical_path),
        "ai06": json_sha(ai_path),
    }
    result["verificador_sha256"] = {
        p.relative_to(ROOT).as_posix(): sha(p)
        for p in sorted(Path(__file__).parent.glob("*.py"))
    }
    return result

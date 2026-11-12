"""Consolidação sem chamadas: revisão explícita não reexecuta o LLM."""

import json
from pathlib import Path
from typing import Any

from app.modules.ai.orchestration.settings import Config
from tests.ai.evaluation.reporting import (
    identity,
    json_sha,
    load_dataset,
    summarize_real,
    valid_plan,
)


def consolidate(deterministic: Path, real: Path, review: Path | None) -> dict[str, Any]:
    det = json.loads(deterministic.read_text("utf-8"))
    live = json.loads(real.read_text("utf-8"))
    rows = live.get("observacoes", {}).get("casos", [])
    evaluated = [r for r in rows if r.get("chamadas")]
    rubric = json.loads(review.read_text("utf-8")) if review else {}
    reviewed = {r["id"]: r for r in rubric.get("casos", [])}
    current = identity()
    same = all(
        det.get(key) == live.get(key) == current[key]
        for key in (
            "configuracao_sha256",
            "politica_sha256",
            "prompts",
            "consulta_geracao",
            "extracao",
            "algoritmo_hash_fontes",
            "fontes_sha256",
            "codigo_sha256",
        )
    )
    bound = rubric.get("execucao_sha256") == json_sha(real)
    reviews_bound = (
        bound
        and bool(evaluated)
        and len(rubric.get("casos", [])) == len(evaluated)
        and len(reviewed) == len(evaluated)
        and set(reviewed) == {r["id"] for r in evaluated}
    )
    goals = Config.load().quality
    supported = sum(
        reviewed[r["id"]].get("fundamentada") is True
        for r in evaluated
        if r["id"] in reviewed
    )
    support_fraction = supported / len(evaluated) if evaluated else 0.0
    reviews_ok = (
        reviews_bound
        and support_fraction >= float(str(goals["supported_answers_fraction"]))
        and all(
            all(
                reviewed[r["id"]].get(field) is True
                for field in ("portugues", "unidades_negacoes", "seguranca")
            )
            for r in evaluated
        )
    )
    eligible = [r for r in rows if r.get("esperado") == "PUBLICADA"]
    valid = sum(valid_plan(r) for r in eligible)
    positives = [r for r in rows if r.get("recuperou_esperado") is not None]
    recalled = sum(bool(r["recuperou_esperado"]) for r in positives)
    obligations = [r for r in rows if r.get("esperado") not in {"PUBLICADA"}]
    expected_ids = {r["id"] for r in load_dataset()["real"]}
    observed_ids = [r.get("id") for r in rows]
    measured = summarize_real(live.get("observacoes", {}))
    latencies = measured["latencia_somente_resposta_ou_ficha_valida"]
    search = measured["busca"]
    requirements = {
        "mesma_configuracao_e_casos": same,
        "deterministico_aprovado": det.get("estado")
        == "DETERMINISTICO_APROVADO_REAL_PENDENTE",
        "amostra_completa": len(observed_ids) == len(expected_ids)
        and set(observed_ids) == expected_ids
        and all(r["estado"] != "PENDENTE_PROVEDOR" for r in rows),
        "casos_obrigatorios": bool(obligations)
        and all(r.get("correto_automatico") for r in obligations),
        "sem_falha_critica": bool(rows)
        and not any(r.get("falha_critica") for r in rows),
        "fichas_validas": bool(eligible)
        and valid / len(eligible) >= float(str(goals["eligible_valid_plan_fraction"])),
        "recuperacao": bool(positives)
        and recalled / len(positives) >= float(str(goals["retrieval_recall_at_5"])),
        "revisao_semantica_vinculada": reviews_bound,
        "revisao_semantica_aprovada": reviews_ok,
        "latencia_de_respostas_validas_medida": all(
            latencies.get(route, {}).get("n", 0) > 0
            and latencies.get(route, {}).get("p95_ms") is not None
            for route in ("DUVIDA", "GERACAO", "ADAPTACAO")
        ),
        "metas_de_latencia": bool(search.get("n"))
        and search.get("p95_ms", float("inf"))
        <= float(str(goals["vector_p95_seconds"])) * 1000
        and all(
            bool(latencies.get(route, {}).get("n"))
            and latencies[route]["p95_ms"] <= float(str(goals[goal])) * 1000
            for route, goal in (
                ("DUVIDA", "target_chat_p95_seconds"),
                ("GERACAO", "target_generation_p95_seconds"),
                ("ADAPTACAO", "target_generation_p95_seconds"),
            )
        ),
    }
    return {
        "schema_version": 1,
        "estado": "APROVADO" if all(requirements.values()) else "PENDENTE_OU_REPROVADO",
        "aceite_ia_real": all(requirements.values()),
        "criterios": requirements,
        "revisao_semantica": {
            "fundamentadas": supported,
            "total": len(evaluated),
            "fracao": support_fraction,
            "limiar_aprovado": float(str(goals["supported_answers_fraction"])),
            "idioma_unidades_seguranca_sem_falhas": reviews_bound
            and all(
                all(
                    reviewed[r["id"]].get(f) is True
                    for f in ("portugues", "unidades_negacoes", "seguranca")
                )
                for r in evaluated
            ),
        },
        "algoritmo_hash": "JSON_CANONICO_V1",
        "entradas_sha256": {
            "deterministico": json_sha(deterministic),
            "real": json_sha(real),
            "revisao": json_sha(review) if review else None,
        },
        "nota": "AI-06 aprovado não substitui o E2E/aceite do MVP em TST-01.",
    }

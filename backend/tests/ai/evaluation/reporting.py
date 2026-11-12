"""Métricas de avaliação; sem inferir suporte semântico a partir de JSON."""

import hashlib
import json
import math
import platform
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(path: Path) -> str:
    from app.contracts.structured import digest

    return digest(json.loads(path.read_text("utf-8-sig")))


def load_dataset() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ROOT / "docs/testes/ai06-casos-v3.json").read_text("utf-8")
    )
    ids = [c["id"] for c in data["cenarios"]]
    expected = {f"SV-{n:02}" for n in range(1, 25)} | {
        f"SC-{n:02}" for n in range(1, 7)
    }
    if len(ids) != len(expected) or set(ids) != expected:
        raise ValueError("Matriz SV/SC incompleta ou duplicada.")
    live = data["real"]
    if len(live) < 24 or len({c["id"] for c in live}) != len(live):
        raise ValueError("Amostra real incompleta ou duplicada.")
    return data


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if not 0 < fraction <= 1 or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Métrica inválida.")
    return sorted(values)[math.ceil(len(values) * fraction) - 1]


def timings(values: list[float]) -> dict[str, float | int | None]:
    return {
        "n": len(values),
        "p50_ms": statistics.median(values) if values else None,
        "p95_ms": percentile(values, 0.95),
    }


def junit(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.stat().st_size > 20 * 1024 * 1024:
        return []
    root = ET.fromstring(path.read_bytes())
    rows = []
    for case in root.iter("testcase"):
        selector = case.attrib.get("classname", "").replace(".", "/") + ".py::"
        selector += case.attrib.get("name", "").split("[", 1)[0]
        status = (
            "FALHA"
            if case.find("failure") is not None or case.find("error") is not None
            else "IGNORADO"
            if case.find("skipped") is not None
            else "APROVADO"
        )
        rows.append(
            {
                "teste": selector,
                "estado": status,
                "segundos": float(case.attrib.get("time", 0)),
            }
        )
    return rows


def scenario_results(
    dataset: dict[str, Any], rows: list[dict[str, Any]], frontend_ok: bool
) -> list[dict[str, Any]]:
    result = []
    for case in dataset["cenarios"]:
        selected = [r for r in rows if r["teste"] in case["testes"]]
        missing = set(case["testes"]) - {r["teste"] for r in selected}
        failed = any(r["estado"] != "APROVADO" for r in selected)
        status = (
            "PENDENTE_REAL"
            if not case["testes"]
            else "PENDENTE"
            if missing
            else "FALHA"
            if failed or (case["exige_frontend"] and not frontend_ok)
            else "APROVADO_DETERMINISTICO"
        )
        result.append(
            {
                "id": case["id"],
                "estado": status,
                "testes": selected,
                "faltantes": sorted(missing),
                "exige_real": case["exige_real"],
            }
        )
    return result


def identity() -> dict[str, Any]:
    from app.modules.ai.orchestration.queries import VERSION as QUERY_VERSION
    from app.modules.ai.orchestration.settings import Config
    from app.modules.ai.policies.triage import Policy
    from app.modules.ai.prompts.v1 import VERSION
    from app.modules.knowledge.ingestion.contracts import ExtractionPolicy

    paths = [
        "docs/testes/ai06-casos-v3.json",
        "docs/testes/casos-triagem-v1.json",
        "docs/testes/rag05-consultas-v1.json",
        "materiais/rag/corpus-inicial.json",
        "docs/testes/ai06-corpus-v2.json",
        "docs/testes/ai06-catalogo-v1.json",
        "materiais/rag/politica-livro-v2.json",
        "materiais/rag/livro-de-apoio.json",
    ]
    return {
        "configuracao_sha256": Config.load().fingerprint,
        "politica_sha256": Policy().fingerprint,
        "prompts": VERSION,
        "modelo": Config.load().model,
        "consulta_geracao": QUERY_VERSION,
        "extracao": ExtractionPolicy().fingerprint,
        "algoritmo_hash_fontes": "JSON_CANONICO_V1",
        "fontes_sha256": {p: json_sha(ROOT / p) for p in paths},
        "codigo_sha256": {
            p: hashlib.sha256(
                (ROOT / p).read_text("utf-8").replace("\r\n", "\n").encode()
            ).hexdigest()
            for p in (
                "backend/app/modules/ai/prompts/v1.py",
                "backend/app/modules/ai/orchestration/settings.py",
                "backend/app/modules/ai/adapters/factory.py",
                "backend/app/modules/ai/adapters/groq.py",
                "backend/app/modules/ai/adapters/gemini.py",
                "backend/app/modules/ai/generation.py",
                "backend/app/modules/ai/orchestration/queries.py",
                "backend/app/modules/ai/orchestration/service.py",
                "backend/app/modules/ai/orchestration/presentation.py",
                "backend/app/modules/knowledge/ingestion/parser.py",
                "backend/app/modules/knowledge/ingestion/contracts.py",
                "backend/tests/ai/evaluation/__main__.py",
                "backend/tests/ai/evaluation/fixtures.py",
                "backend/tests/ai/test_evaluation_real.py",
                "backend/tests/ai/evaluation/reporting.py",
                "backend/tests/ai/evaluation/consolidation.py",
                "backend/tests/ai/evaluation/resume.py",
                "backend/uv.lock",
            )
        },
        "ambiente": {
            "python": platform.python_version(),
            "sistema": platform.platform(),
            "cpu": platform.processor(),
        },
        "custos": {
            "plano_previsto": "gratuito",
            "valor_monetario": None,
            "nota": "API informa tokens, não fatura. Sem contratação/fallback pago.",
        },
    }


def redact_secrets(body: str) -> str:
    import os

    for name in ("GROQ_API_KEY", "GEMINI_API_KEY"):
        key = os.environ.get(name, "")
        if key:
            body = body.replace(key, "[CREDENCIAL_REMOVIDA]")
    return body


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")

    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    body = redact_secrets(body)
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(path)


def valid_plan(row: dict[str, Any]) -> bool:
    return row.get("estado") == "PUBLICADA" and row.get("correto_automatico") is True


def summarize_real(data: dict[str, Any]) -> dict[str, Any]:
    from app.modules.ai.orchestration.settings import Config

    cases = data.get("casos", [])
    eligible = [r for r in cases if r.get("esperado") == "PUBLICADA"]
    positives = [r for r in cases if r.get("recuperou_esperado") is not None]
    physical = [c for r in cases for c in r.get("consumo", []) if c["chamadas_fisicas"]]
    usage = [c["uso"] for c in physical if c.get("uso") is not None]
    missing = sum(r.get("estado") == "PENDENTE_PROVEDOR" for r in cases)
    limits = Config.load().quality
    return {
        "casos_planejados": len(load_dataset()["real"]),
        "casos_executados": len(cases) - missing,
        "casos_pendentes_provedor": missing,
        "falhas_criticas": sum(bool(r.get("falha_critica")) for r in cases),
        "casos_corretos_automaticos": sum(
            bool(r.get("correto_automatico")) for r in cases
        ),
        "recall_amostra": {
            "numerador": sum(bool(r["recuperou_esperado"]) for r in positives),
            "denominador": len(positives),
        },
        "fichas_elegiveis_validas": {
            "numerador": sum(valid_plan(r) for r in eligible),
            "denominador": len(eligible),
        },
        "respostas_fundamentadas": {
            "numerador": None,
            "denominador": None,
            "estado": "REVISAO_SEMANTICA_PENDENTE",
        },
        "chamadas_fisicas": len(physical),
        "consumo_desconhecido": len(physical) - len(usage),
        "tokens_conhecidos": sum(u["total_tokens"] for u in usage),
        "tokens_entrada_conhecidos": sum(u["prompt_tokens"] for u in usage),
        "tokens_saida_conhecidos": sum(u["completion_tokens"] for u in usage),
        "rotas": data.get("rotas", {}),
        "latencia_somente_resposta_ou_ficha_valida": {
            route: timings(
                [
                    r["total_ms"]
                    for r in cases
                    if r.get("rota") == route
                    and r.get("estado") in {"RESPOSTA_PRONTA", "PUBLICADA"}
                    and r.get("correto_automatico") is True
                    and r.get("chamadas")
                    and "total_ms" in r
                ]
            )
            for route in ("DUVIDA", "GERACAO", "ADAPTACAO")
        },
        "busca": data.get("busca", {}),
        "limiares": limits,
        "aceite_ia_real": False,
        "nota": "JSON/referências válidos não aprovam suporte, tradução ou prescrição.",
    }

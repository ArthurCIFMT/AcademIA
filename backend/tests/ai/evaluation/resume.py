"""Retomada explícita de ensaio, sem retry e sem escolher entre respostas válidas."""

import json
from pathlib import Path
from typing import Any

from app.modules.ai.orchestration.settings import Config
from tests.ai.evaluation.reporting import (
    identity,
    json_sha,
    load_dataset,
    summarize_real,
    timings,
    valid_plan,
)

IDENTITY_KEYS = (
    "configuracao_sha256",
    "politica_sha256",
    "prompts",
    "consulta_geracao",
    "extracao",
    "algoritmo_hash_fontes",
    "fontes_sha256",
    "codigo_sha256",
    "ambiente",
)


def select_cases(data: dict[str, Any], requested: str | None) -> list[dict[str, Any]]:
    if requested is None:
        return list(data["real"])
    ids = requested.split(",")
    known = {r["id"] for r in data["real"]}
    if not ids or len(set(ids)) != len(ids) or not set(ids) <= known:
        raise ValueError("Informe IDs conhecidos e distintos, separados por vírgula.")
    return [r for r in data["real"] if r["id"] in ids]


def observations(rows: list[dict[str, Any]], cold_ms: float | None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "casos": rows,
        "inicializacao_e5_ms": cold_ms,
        "rotas": {
            route: timings(
                [r["total_ms"] for r in rows if r["rota"] == route and "total_ms" in r]
            )
            for route in ("DUVIDA", "GERACAO", "ADAPTACAO")
        },
        "busca": timings([b["parede_ms"] for r in rows for b in r.get("buscas", [])]),
        "limites": [
            "Serviço real; exclui fixture, aquecimento, HTTP/UI e pausas.",
            "Corpus delimitado; não comprova cobertura clínica ampla.",
            "Publicações/ataques ficam no banco e índice isolados.",
        ],
    }


def technical_acceptance(rows: list[dict[str, Any]], expected_count: int) -> bool:
    if len(rows) != expected_count or any(r.get("falha_critica") for r in rows):
        return False
    eligible = [r for r in rows if r.get("esperado") == "PUBLICADA"]
    required = [r for r in rows if r.get("esperado") != "PUBLICADA"]
    threshold = float(str(Config.load().quality["eligible_valid_plan_fraction"]))
    return all(r.get("correto_automatico") for r in required) and (
        not eligible
        or sum(valid_plan(r) for r in eligible) / len(eligible) >= threshold
    )


def unavailable(row: dict[str, Any]) -> bool:
    return row["estado"] == "PENDENTE_PROVEDOR" or row.get("motivo") in {
        "QUOTA_EXCEDIDA",
        "TRANSPORTE_INDISPONIVEL",
        "PROVEDOR_INDISPONIVEL",
        "CREDENCIAL_RECUSADA",
    }


def merge_real(paths: list[Path]) -> dict[str, Any]:
    if not 2 <= len(paths) <= 16 or len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("Use de duas a dezesseis partes distintas.")
    current = identity()
    data = load_dataset()
    known = {r["id"] for r in data["real"]}
    selected: dict[str, dict[str, Any]] = {}
    origins: dict[str, str] = {}
    previous = []
    parts = []
    metrics = []
    for path in paths:
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Relatório excedido.")
        report = json.loads(path.read_text("utf-8"))
        if report.get("modo") != "real" or any(
            report.get(k) != current[k] for k in IDENTITY_KEYS
        ):
            raise ValueError("Configuração, código ou ambiente incompatível.")
        rows = report.get("observacoes", {}).get("casos", [])
        ids = [r["id"] for r in rows]
        if len(ids) != len(set(ids)) or not set(ids) <= known:
            raise ValueError("IDs inválidos ou repetidos na parte.")
        digest = json_sha(path)
        parts.append(
            {
                "arquivo": path.parent.name + "/" + path.name,
                "sha256": digest,
                "casos": ids,
                "inicializacao_e5_ms": report.get("observacoes", {}).get(
                    "inicializacao_e5_ms"
                ),
                "testes": report.get("testes", []),
            }
        )
        metrics.append(summarize_real(report.get("observacoes", {})))
        for row in rows:
            old = selected.get(row["id"])
            if old is not None:
                if not unavailable(old):
                    raise ValueError(
                        "Não substituir resposta concluída ou falha de qualidade."
                    )
                if old["estado"] != "PENDENTE_PROVEDOR":
                    previous.append({"parte_sha256": origins[row["id"]], "caso": old})
            selected[row["id"]] = row
            origins[row["id"]] = digest
    if set(selected) != known:
        raise ValueError("Conjunto ainda não contém todos os casos previstos.")
    ordered = [selected[r["id"]] for r in data["real"]]
    observed = observations(ordered, None)
    complete = technical_acceptance(ordered, len(known))
    return {
        "schema_version": 1,
        "modo": "real_multi_execucao",
        **current,
        "estado": "EXECUCOES_REAIS_COMPLETADAS" if complete else "FALHA",
        "aceite_ia_real": False,
        "observacoes": observed,
        "metricas": summarize_real(observed),
        "partes": parts,
        "tentativas_anteriores": previous,
        "consumo_incluindo_partes": {
            key: sum(m[key] for m in metrics)
            for key in ("chamadas_fisicas", "tokens_conhecidos", "consumo_desconhecido")
        },
        "nota": (
            "Partes explícitas de mesma configuração. Falhas de provedor preservadas; "
            "não constitui retry da mesma execução nem seleção da melhor resposta. "
            "Só consolidação com revisão pode aprovar."
        ),
    }

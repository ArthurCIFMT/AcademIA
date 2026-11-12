import copy
import json
from pathlib import Path

import pytest

from tests.ai.evaluation.reporting import identity, load_dataset
from tests.ai.evaluation.resume import merge_real, observations, select_cases


def parts(tmp_path: Path) -> tuple[Path, Path]:
    rows = [
        {
            "id": c["id"],
            "rota": c["rota"],
            "estado": c["esperado"]
            if c["esperado"] != "SEM_EFEITO_PROIBIDO"
            else "RESPOSTA_PRONTA",
            "esperado": c["esperado"],
            "correto_automatico": True,
            "total_ms": 1.0,
            "chamadas": [],
            "consumo": [],
            "buscas": [],
        }
        for c in load_dataset()["real"]
    ]
    first = copy.deepcopy(rows)
    first[13].update(
        estado="FALHA",
        motivo="QUOTA_EXCEDIDA",
        correto_automatico=False,
        consumo=[{"chamadas_fisicas": 1, "uso": None}],
    )
    for r in first[14:]:
        r.update(estado="PENDENTE_PROVEDOR", correto_automatico=False)
        r.pop("total_ms")
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    for path, values in ((a, first), (b, rows[13:])):
        path.write_text(
            json.dumps(
                {"modo": "real", **identity(), "observacoes": observations(values, 1.0)}
            )
        )
    return a, b


def test_resume_requires_explicit_known_distinct_ids() -> None:
    data = load_dataset()
    assert len(select_cases(data, None)) == 27
    assert [r["id"] for r in select_cases(data, "L14,L15")] == ["L14", "L15"]
    for value in ("", "L99", "L14,L14"):
        with pytest.raises(ValueError):
            select_cases(data, value)


def test_merge_retains_provider_failure_and_does_not_approve_without_review(
    tmp_path: Path,
) -> None:
    a, b = parts(tmp_path)
    report = merge_real([a, b])
    assert len(report["observacoes"]["casos"]) == 27
    assert report["estado"] == "EXECUCOES_REAIS_COMPLETADAS"
    assert report["tentativas_anteriores"][0]["caso"]["motivo"] == "QUOTA_EXCEDIDA"
    assert report["consumo_incluindo_partes"]["consumo_desconhecido"] == 1
    assert not report["aceite_ia_real"]


@pytest.mark.parametrize("failure", ["schema", "different_code", "repeat_success"])
def test_merge_never_selects_better_response_or_mixes_versions(
    tmp_path: Path, failure: str
) -> None:
    a, b = parts(tmp_path)
    first = json.loads(a.read_text())
    second = json.loads(b.read_text())
    if failure == "schema":
        first["observacoes"]["casos"][13].update(
            estado="SCHEMA_INVALIDO", motivo="RESTRICAO_OU_CONTRATO_INVALIDO"
        )
        a.write_text(json.dumps(first))
    elif failure == "different_code":
        second["prompts"] = "outra-versao"
        b.write_text(json.dumps(second))
    else:
        second["observacoes"]["casos"].append(first["observacoes"]["casos"][0])
        b.write_text(json.dumps(second))
    with pytest.raises(ValueError):
        merge_real([a, b])


def test_technical_fraction_preserves_all_required_cases() -> None:
    from tests.ai.evaluation.resume import technical_acceptance

    rows = [
        {"esperado": "PUBLICADA", "estado": "PUBLICADA", "correto_automatico": True}
        for _ in range(8)
    ]
    rows[0].update(estado="DADOS_INSUFICIENTES", correto_automatico=False)
    assert technical_acceptance(rows, 8)
    rows[1].update(estado="FALHA", correto_automatico=False)
    assert not technical_acceptance(rows, 8)
    rows[1].update(estado="PUBLICADA", correto_automatico=True)
    rows.append(
        {"esperado": "BLOQUEADA", "estado": "PUBLICADA", "correto_automatico": False}
    )
    assert not technical_acceptance(rows, 9)
    rows[-1].update(estado="BLOQUEADA", correto_automatico=True, falha_critica=True)
    assert not technical_acceptance(rows, 9)

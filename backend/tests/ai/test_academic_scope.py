from copy import deepcopy

import pytest

from tests.ai.evaluation.fixtures import within_demo_scope
from tests.ai.evaluation.reporting import load_dataset, summarize_real
from tests.ai.evaluation.resume import technical_acceptance


def test_academic_sample_preserves_security_and_changes_unsupported_progression() -> (
    None
):
    data = load_dataset()
    assert data["versao_amostra"] == 3 and len(data["real"]) == 27
    rows = {c["id"]: c for c in data["real"]}
    assert rows["L18"]["series_base"] == 1
    assert rows["L19"]["series_base"] == 2
    assert rows["L23"]["origem"] == "SC-01" and rows["L24"]["origem"] == "SC-02"
    assert rows["L21"]["esperado"] == "BLOQUEADA"
    for id in ("L13", "L14", "L15", "L16", "L17"):
        assert rows[id]["limites_ficha"]["max_series"] == 2
        assert rows[id]["limites_ficha"]["max_itens_por_dia"] == 2
    assert rows["L25"]["esperado"] == rows["L26"]["esperado"] == "DADOS_INSUFICIENTES"
    assert rows["L27"]["esperado"] == "BLOQUEADA"


@pytest.mark.parametrize("invalid", ["sets", "items", "days", "missing", "boolean"])
def test_demo_limits_reject_excess_without_requiring_optional_values(
    invalid: str,
) -> None:
    case = {"limites_ficha": {"max_dias": 2, "max_itens_por_dia": 2, "max_series": 2}}
    good = {"dias": [{"itens": [{"series": 2, "carga_kg": None, "cadencia": None}]}]}
    assert within_demo_scope(case, good)
    bad = deepcopy(good)
    if invalid == "sets":
        bad["dias"][0]["itens"][0]["series"] = 4
    elif invalid == "items":
        bad["dias"][0]["itens"] *= 3
    elif invalid == "days":
        bad["dias"] *= 3
    elif invalid == "boolean":
        bad["dias"][0]["itens"][0]["series"] = True
    else:
        del bad["dias"][0]["itens"][0]["series"]
    assert not within_demo_scope(case, bad)
    assert not within_demo_scope(case, None)
    assert within_demo_scope({}, None)


def test_published_plan_outside_request_is_not_counted_as_valid() -> None:
    row = {
        "estado": "PUBLICADA",
        "esperado": "PUBLICADA",
        "correto_automatico": False,
        "conforme_escopo_academico": False,
        "rota": "GERACAO",
        "total_ms": 1.0,
        "chamadas": [{}],
    }
    assert not technical_acceptance([row], 1)
    report = summarize_real({"casos": [row]})
    assert report["fichas_elegiveis_validas"] == {"numerador": 0, "denominador": 1}
    assert report["latencia_somente_resposta_ou_ficha_valida"]["GERACAO"]["n"] == 0

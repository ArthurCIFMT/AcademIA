from pathlib import Path

import pytest

from tests.ai.evaluation.reporting import (
    junit,
    load_dataset,
    percentile,
    scenario_results,
    timings,
)


def test_matrix_is_complete_and_selectors_exist() -> None:
    import ast

    from tests.ai.evaluation.reporting import ROOT

    data = load_dataset()
    assert len(data["cenarios"]) == 30 and len(data["real"]) == 24
    for case in data["cenarios"]:
        for selector in case["testes"]:
            file, name = selector.split("::")
            tree = ast.parse((ROOT / "backend" / file).read_text("utf-8"))
            assert any(
                isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == name
                for n in tree.body
            ), selector


def test_percentiles_and_empty_routes_do_not_invent_measurements() -> None:
    assert percentile([100, 1, 5, 10], 0.95) == 100
    assert timings([]) == {"n": 0, "p50_ms": None, "p95_ms": None}
    assert timings([3, 1, 2])["p50_ms"] == 2
    with pytest.raises(ValueError):
        percentile([float("nan")], 0.95)


def test_missing_skipped_or_failed_test_never_approves_scenario(tmp_path: Path) -> None:
    file = tmp_path / "junit.xml"
    file.write_text(
        "<testsuites><testsuite>"
        '<testcase classname="tests.ai.fake" name="test_case[a]" time="1"/>'
        '<testcase classname="tests.ai.fake" name="test_case[b]"><skipped/></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    rows = junit(file)
    dataset = {
        "cenarios": [
            {
                "id": "SC-04",
                "testes": ["tests/ai/fake.py::test_case"],
                "exige_real": False,
                "exige_frontend": True,
            }
        ]
    }
    assert scenario_results(dataset, rows, True)[0]["estado"] == "FALHA"
    assert scenario_results(dataset, [], True)[0]["estado"] == "PENDENTE"
    assert not junit(tmp_path / "absent.xml")


def test_real_summary_never_treats_missing_or_schema_as_semantic_approval() -> None:
    from tests.ai.evaluation.reporting import summarize_real

    report = summarize_real(
        {
            "casos": [
                {"id": "L01", "estado": "PENDENTE_PROVEDOR"},
                {
                    "id": "L13",
                    "estado": "ABSTENCAO",
                    "esperado": "PUBLICADA",
                    "correto_automatico": False,
                    "recuperou_esperado": False,
                    "consumo": [{"chamadas_fisicas": 1, "uso": None}],
                },
            ]
        }
    )
    assert not report["aceite_ia_real"]
    assert report["casos_executados"] == 1
    assert report["consumo_desconhecido"] == 1
    assert report["fichas_elegiveis_validas"] == {"numerador": 0, "denominador": 1}
    assert report["respostas_fundamentadas"]["numerador"] is None
    assert report["latencia_somente_resposta_ou_ficha_valida"]["GERACAO"]["n"] == 0


def test_consolidation_does_not_accept_missing_semantic_review(tmp_path: Path) -> None:
    import json

    from tests.ai.evaluation.consolidation import consolidate

    det = tmp_path / "det.json"
    real = tmp_path / "real.json"
    det.write_text(json.dumps({"estado": "DETERMINISTICO_APROVADO_REAL_PENDENTE"}))
    real.write_text(json.dumps({"observacoes": {"casos": []}}))
    result = consolidate(det, real, None)
    assert not result["aceite_ia_real"]
    assert not result["criterios"]["amostra_completa"]
    assert not result["criterios"]["revisao_semantica_vinculada"]


def test_real_literature_never_adds_unapproved_triage_purpose() -> None:
    from tests.ai.evaluation.live_support import guard_literature

    digest = "cbed0ec7227152c6a3b7d58c37140ed0cb2ef136ac0414735c2ff73474241798"
    guard_literature(digest, ["DUVIDAS", "GERACAO_GERAL"])
    with pytest.raises(ValueError):
        guard_literature(digest, ["TRIAGEM"])
    with pytest.raises(ValueError):
        guard_literature("0" * 64, ["DUVIDAS"])


def test_consolidation_rejects_repeated_cases_despite_count(tmp_path: Path) -> None:
    import json

    from tests.ai.evaluation.consolidation import consolidate

    det = tmp_path / "det.json"
    real = tmp_path / "real.json"
    det.write_text(json.dumps({"estado": "DETERMINISTICO_APROVADO_REAL_PENDENTE"}))
    real.write_text(
        json.dumps(
            {
                "observacoes": {
                    "casos": [
                        {
                            "id": "L01",
                            "estado": "RESPOSTA_PRONTA",
                            "correto_automatico": True,
                        }
                        for _ in range(24)
                    ]
                }
            }
        )
    )
    assert not consolidate(det, real, None)["criterios"]["amostra_completa"]


def test_synthetic_attack_is_refused_outside_test_database() -> None:
    from unittest.mock import MagicMock

    from app.modules.knowledge.schemas import Metadata
    from tests.ai.evaluation.live_support import index_source

    sessions = MagicMock()
    connection = (
        sessions.begin.return_value.__enter__.return_value.connection.return_value
    )
    connection.scalar.return_value = "academia_dev"
    with pytest.raises(RuntimeError, match="academia_test"):
        index_source(
            sessions,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Path("."),
            body=b"fixture",
            format="TXT",
            catalog_id="AI06-ATTACK",
            metadata=Metadata(
                titulo="Fixture",
                origem_url="https://example.test",
                licenca="Fixture",
                idioma="pt-BR",
                finalidades=["DUVIDAS"],
                limites="Teste",
            ),
            spans=[],
            purposes=["DUVIDAS"],
            synthetic_attack=True,
        )


def test_real_mode_without_credential_records_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from tests.ai.evaluation.__main__ import main

    output = tmp_path / "run"
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        "sys.argv", ["evaluation", "--mode", "real", "--output", str(output)]
    )
    assert main() == 2
    report = json.loads((output / "relatorio.json").read_text("utf-8"))
    assert report["estado"] == "PENDENTE_CREDENCIAL"
    assert not report["aceite_ia_real"]


def test_artifact_writer_never_persists_provider_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.ai.evaluation.reporting import write_json

    key = "gsk_synthetic_do_not_publish"
    monkeypatch.setenv("GROQ_API_KEY", key)
    output = tmp_path / "report.json"
    write_json(output, {"nested": [{"answer": "token: " + key}]})
    assert key not in output.read_text("utf-8")
    assert "[CREDENCIAL_REMOVIDA]" in output.read_text("utf-8")


def test_review_hash_is_portable_across_json_format_and_line_endings(
    tmp_path: Path,
) -> None:
    from tests.ai.evaluation.reporting import json_sha

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_bytes(b'{"a":1,"b":2}\n')
    second.write_bytes(b'{\r\n  "b": 2,\r\n  "a": 1\r\n}\r\n')
    assert json_sha(first) == json_sha(second)
    second.write_text('{"a":2,"b":2}', encoding="utf-8")
    assert json_sha(first) != json_sha(second)

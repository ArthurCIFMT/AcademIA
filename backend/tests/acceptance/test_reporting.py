import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from tests.acceptance.__main__ import (
    ai_gate,
    browser_rows,
    local_acceptance,
    require_empty_test_database,
)


def sample() -> dict[str, Any]:
    return {
        "suites": [
            {
                "specs": [
                    {
                        "title": f"E2E-{n:02} cenário",
                        "tests": [
                            {
                                "status": "expected",
                                "results": [{"status": "passed", "duration": 1}],
                            }
                        ],
                    }
                    for n in range(1, 9)
                ]
            }
        ]
    }


def test_only_complete_distinct_browser_cases_pass() -> None:
    rows = browser_rows(sample())
    assert local_acceptance(rows)
    assert not local_acceptance(rows[:-1])
    repeated = copy.deepcopy(rows)
    repeated[-1]["id"] = repeated[0]["id"]
    assert not local_acceptance(repeated)


@pytest.mark.parametrize("status", ["unexpected", "skipped", "flaky"])
def test_skips_failures_and_retries_are_never_local_acceptance(status: str) -> None:
    raw = sample()
    raw["suites"][0]["specs"][0]["tests"][0]["status"] = status
    assert not local_acceptance(browser_rows(raw))


def test_expected_status_with_two_attempts_is_not_success() -> None:
    raw = sample()
    test = raw["suites"][0]["specs"][0]["tests"][0]
    test["results"].insert(0, {"status": "failed", "duration": 1})
    assert not local_acceptance(browser_rows(raw))


def test_real_ai_gate_remains_pending_and_hash_bound(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    path.write_text(json.dumps({"aceite_ia_real": False, "estado": "PENDENTE"}))
    before = ai_gate(path)
    assert not before["aprovado"]
    path.write_text(json.dumps({"aceite_ia_real": True, "estado": "APROVADO"}))
    after = ai_gate(path)
    assert after["aprovado"] and before["sha256"] != after["sha256"]
    path.write_text("{}")
    assert not ai_gate(path)["aprovado"]


def test_database_guard_preserves_existing_schema() -> None:
    connection = MagicMock()
    connection.scalar.side_effect = ["academia_test", "academia"]
    with pytest.raises(RuntimeError, match="não apaga"):
        require_empty_test_database(connection)
    assert len(connection.scalar.call_args_list) == 2


def test_database_guard_rejects_development_database() -> None:
    connection = MagicMock()
    connection.scalar.return_value = "academia_dev"
    with pytest.raises(RuntimeError, match="academia_test"):
        require_empty_test_database(connection)
    assert connection.scalar.call_count == 1

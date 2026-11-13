"""Consolidação sem navegador, banco ou chamadas externas."""

import argparse
from pathlib import Path

from tests.acceptance.__main__ import ROOT
from tests.acceptance.consolidation import consolidate
from tests.ai.evaluation.reporting import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--e2e", type=Path, default=ROOT / "docs/testes/tst01-resultado.json"
    )
    parser.add_argument(
        "--critical", type=Path, default=ROOT / "docs/testes/tst01-criticos.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Escolha uma saída nova; não sobrescrever evidências.")
    result = consolidate(args.e2e, args.critical)
    write_json(args.output, result)
    print(result["estado"])
    return 0 if result["aceite_mvp"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

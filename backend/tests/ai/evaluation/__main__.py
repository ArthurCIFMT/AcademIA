"""Runner explícito: python -m tests.ai.evaluation --mode ... --output ..."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tests.ai.evaluation.reporting import (
    ROOT,
    identity,
    junit,
    load_dataset,
    scenario_results,
    summarize_real,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["deterministic", "real", "consolidate", "merge"],
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--deterministic-report", type=Path)
    parser.add_argument("--real-report", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument(
        "--cases", help="Retomada explícita: IDs separados por vírgula."
    )
    parser.add_argument("--part", type=Path, action="append")
    args = parser.parse_args()
    if args.cases and args.mode != "real":
        parser.error("--cases só se aplica a nova execução real.")

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Use uma pasta de saída nova para preservar evidências.")
    output.mkdir(parents=True, exist_ok=True)
    if args.mode == "merge":
        from tests.ai.evaluation.resume import merge_real

        try:
            merged = merge_real(args.part or [])
        except (ValueError, OSError, KeyError) as error:
            parser.error(str(error))
        write_json(output / "relatorio.json", merged)
        print(merged["estado"])
        return 0 if merged["estado"] == "EXECUCOES_REAIS_COMPLETADAS" else 1
    if args.mode == "consolidate":
        if not args.deterministic_report or not args.real_report:
            parser.error("Informe os dois relatórios; consolidação não chama o modelo.")
        from tests.ai.evaluation.consolidation import consolidate

        decision = consolidate(args.deterministic_report, args.real_report, args.review)
        write_json(output / "relatorio.json", decision)
        print(decision["estado"])
        return 0 if decision["aceite_ia_real"] else 1
    dataset = load_dataset()
    from tests.ai.evaluation.resume import select_cases

    try:
        requested = select_cases(dataset, args.cases)
    except ValueError as error:
        parser.error(str(error))
    report = {
        "schema_version": 1,
        "modo": args.mode,
        **identity(),
        "aceite_ia_real": False,
        "casos_solicitados": [r["id"] for r in requested],
        "amostra_parcial": bool(args.cases),
    }
    env = dict(os.environ)
    env["ACADEMIA_AI_EVALUATION_OUTPUT"] = str(output)
    env["ACADEMIA_TEST_EMBEDDINGS_REAL"] = "1"
    if args.mode == "real":
        from app.modules.ai.adapters.factory import credential_name
        from app.modules.ai.orchestration.settings import Config

        key_name = credential_name(Config.load())
        if not env.get(key_name, "").strip():
            report.update(estado="PENDENTE_CREDENCIAL", casos=[])
            write_json(output / "relatorio.json", report)
            print(f"Ensaio real pendente: configure {key_name} no ambiente local.")
            return 2
        env["ACADEMIA_AI_REAL"] = "1"
        if args.cases:
            env["ACADEMIA_AI_CASE_IDS"] = args.cases
        targets = ["tests/ai/test_evaluation_real.py"]
    else:
        targets = sorted({t for c in dataset["cenarios"] for t in c["testes"]})
        targets += ["tests/contracts"]
        from app.modules.ai.orchestration.settings import Config

        if Config.load().provider == "gemini":
            targets += [
                "tests/ai/test_gemini.py",
                "tests/ai/test_gemini_integration.py",
            ]
        env["ACADEMIA_RAG_REPORT"] = str(output / "recuperacao-real.json")
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "--tb=short",
        "-q",
        "--junitxml",
        str(output / "backend.xml"),
        "--basetemp",
        str(output / "tmp"),
        *targets,
    ]
    run = subprocess.run(command, cwd=ROOT / "backend", env=env, capture_output=True)
    (output / "backend.log").write_bytes(run.stdout + run.stderr)
    rows = junit(output / "backend.xml")
    if args.mode == "real":
        observed = output / "observacoes.json"
        data = json.loads(observed.read_text("utf-8")) if observed.is_file() else {}
        report.update(
            estado="EXECUTADO" if run.returncode == 0 else "FALHA",
            observacoes=data,
            metricas=summarize_real(data),
            testes=rows,
            nota="Revisão semântica é separada; não inferir suporte pelo schema.",
        )
    else:
        fe = None
        if args.node:
            fe_command = [
                args.node,
                "node_modules/vitest/vitest.mjs",
                "run",
                "--maxWorkers=1",
                "--reporter=json",
                "--outputFile",
                str(output / "frontend.json"),
                "src/features/training-chat",
                "src/features/ai-training",
                "src/features/training-review",
            ]
            fe = subprocess.run(
                fe_command,
                cwd=ROOT / "frontend",
                env={
                    k: v
                    for k, v in env.items()
                    if k not in {"GROQ_API_KEY", "GEMINI_API_KEY"}
                },
                capture_output=True,
            )
            (output / "frontend.log").write_bytes(fe.stdout + fe.stderr)
        frontend_ok = (
            fe is not None
            and fe.returncode == 0
            and (output / "frontend.json").is_file()
        )
        scenarios = scenario_results(dataset, rows, frontend_ok)
        passed = (
            run.returncode == 0
            and frontend_ok
            and all(
                c["estado"] in {"APROVADO_DETERMINISTICO", "PENDENTE_REAL"}
                for c in scenarios
            )
        )
        report.update(
            estado="DETERMINISTICO_APROVADO_REAL_PENDENTE" if passed else "FALHA",
            cenarios=scenarios,
            frontend_aprovado=frontend_ok,
            testes_backend=len(rows),
            codigo_backend=run.returncode,
            codigo_frontend=fe.returncode if fe else None,
            nota="Resposta/tradução e SV-20 exigem LLM real.",
        )
    write_json(output / "relatorio.json", report)
    print(report["estado"])
    print(f"Relatório gravado em {output / 'relatorio.json'}")
    return 0 if run.returncode == 0 and report["estado"] != "FALHA" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Navegador + HTTP + PostgreSQL reais; IA controlada, aceite real separado."""

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, func, select, text
from starlette.types import ASGIApp, Receive, Scope, Send

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.audit.models import AuditRecord
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.models import Notification
from app.modules.training.workout_models import WorkoutVersion
from tests.acceptance.fixtures import BrowserAI, seed_people
from tests.ai.evaluation.reporting import json_sha, write_json

ROOT = Path(__file__).resolve().parents[3]


class SerializedHTTP:
    """Savepoints da conexão única não são teste de carga/concorrência."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.lock = asyncio.Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        async with self.lock:
            await self.app(scope, receive, send)


def browser_rows(value: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for suite in value.get("suites", []):
        rows.extend(browser_rows(suite))
    for spec in value.get("specs", []):
        for test in spec.get("tests", []):
            results = test.get("results", [])
            rows.append(
                {
                    "id": spec["title"].split(" ", 1)[0],
                    "titulo": spec["title"],
                    "estado": test.get("status"),
                    "tentativas": len(results),
                    "navegador": next(
                        (
                            a.get("description")
                            for a in test.get("annotations", [])
                            if a.get("type") == "navegador"
                        ),
                        None,
                    ),
                    "duracao_ms": sum(r.get("duration", 0) for r in results),
                    "passou": test.get("status") == "expected"
                    and len(results) == 1
                    and results[0].get("status") == "passed",
                }
            )
    return rows


def local_acceptance(rows: list[dict[str, Any]]) -> bool:
    expected = {f"E2E-{n:02}" for n in range(1, 9)}
    ids = [row["id"] for row in rows]
    return (
        len(ids) == len(expected)
        and set(ids) == expected
        and all(row["passou"] for row in rows)
    )


def runtime_identity() -> dict[str, str]:
    files = list((ROOT / "backend/app").rglob("*.py"))
    files += [
        p
        for p in (ROOT / "frontend/src").rglob("*")
        if p.suffix in {".ts", ".tsx", ".css"}
    ]
    files += list((ROOT / "backend/tests/acceptance").glob("*.py"))
    files += list((ROOT / "frontend/tests/e2e").glob("*.ts"))
    files += [
        ROOT / "backend/uv.lock",
        ROOT / "frontend/package-lock.json",
        ROOT / "frontend/vite.config.ts",
        ROOT / "frontend/package.json",
        ROOT / "docs/testes/tst01-cenarios.json",
    ]
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(
            p.read_text("utf-8").replace("\r\n", "\n").encode()
        ).hexdigest()
        for p in sorted(files)
    }


def ai_gate(path: Path) -> dict[str, Any]:
    # Documento faltante/alterado nunca vira aceite por conveniência.
    data = json.loads(path.read_text("utf-8-sig"))
    return {
        "arquivo": "docs/testes/ai06-consolidacao.json",
        "sha256": json_sha(path),
        "aprovado": data.get("aceite_ia_real") is True,
        "estado": data.get("estado"),
    }


def require_empty_test_database(connection: Connection) -> None:
    check_database(connection, "test")
    if connection.scalar(text("SELECT to_regnamespace('academia')")) is not None:
        raise RuntimeError("E2E exige academia_test vazio; não apaga schema existente.")
    if not connection.scalar(text("SELECT pg_try_advisory_xact_lock(74810319)")):
        raise RuntimeError("Outro ensaio E2E está usando o banco.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--channel", choices=["msedge", "chromium"], default="msedge")
    parser.add_argument("--frontend-port", type=int, default=5187)
    args = parser.parse_args()
    if not args.node or not 1024 <= args.frontend_port <= 65535:
        parser.error("Configure Node 24 e porta local válida.")
    if os.environ.get("ACADEMIA_E2E") != "1":
        parser.error("Defina ACADEMIA_E2E=1 para o ensaio isolado.")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Use diretório novo; não sobrescrever evidências.")
    if not (ROOT / "frontend/node_modules/@playwright/test/cli.js").is_file():
        parser.error("Execute npm ci no frontend para instalar os testes E2E.")
    node_version = subprocess.check_output([args.node, "--version"], text=True).strip()
    if not node_version.startswith("v24."):
        parser.error("O ensaio usa Node 24 conforme ADR-001.")
    output.mkdir(parents=True, exist_ok=True)
    origin = f"http://127.0.0.1:{args.frontend_port}"
    with httpx.Client(trust_env=False, timeout=5) as client:
        client.get("http://127.0.0.1:8025/api/v1/messages").raise_for_status()
    # Só o Mailpit local recebe mensagens sintéticas; nenhum segredo real é necessário.
    os.environ.pop("GROQ_API_KEY", None)
    os.environ["ACADEMIA_SMTP_HOST"] = "127.0.0.1"
    os.environ["ACADEMIA_SMTP_PORT"] = "1025"
    os.environ["ACADEMIA_SMTP_SENDER"] = "e2e@academia.example.test"
    engine = create_database_engine("test")
    report: dict[str, Any] = {
        "schema_version": 1,
        "modo": "E2E_HTTP_REAL_IA_CONTROLADA",
        "node": node_version,
        "ai06": ai_gate(ROOT / "docs/testes/ai06-consolidacao.json"),
        "codigo_sha256": runtime_identity(),
        "aceite_mvp": False,
        "testes_locais_aprovados": False,
        "limites": [
            "IA/embeddings/trecho são fixtures; Qdrant/PG/HTTP/navegador/SMTP reais.",
            "HTTP serializado para savepoints; não mede concorrência/carga.",
            "Não aprova qualidade/latência do LLM nem substitui AI-06.",
            "Sem Docker, sem gravação em academia_dev ou literatura de uso.",
        ],
    }
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                require_empty_test_database(connection)
                config = Config(str(ROOT / "database/alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                report["migration"] = connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
                sessions = create_session_factory(connection)
                password, suffix = secrets.token_urlsafe(24), secrets.token_hex(4)
                people, users = seed_people(sessions, password, suffix)
                report["bootstrap_idempotente"] = True
                # Equipamentos são cadastrados pela UI no primeiro cenário.
                fixtures = output / "fixture-privada.json"
                write_json(fixtures, {"usuarios": users, "sufixo": suffix})
                ai = BrowserAI(
                    sessions,
                    people["admin"],
                    people["manual"].user_id,
                    output / "corpus-fixture",
                )
                try:
                    app = create_app(
                        identity_sessions=sessions,
                        auth_settings=AuthSettings(
                            origin=origin, allow_local_http=True
                        ),
                    )
                    app.add_middleware(SerializedHTTP)
                    with ExitStack() as stack:
                        stack.enter_context(
                            patch("app.modules.ai.http.GenerationService", ai.generator)
                        )
                        stack.enter_context(
                            patch(
                                "app.modules.ai.chat.service.GenerationService",
                                ai.generator,
                            )
                        )
                        sock = stack.enter_context(socket.socket())
                        sock.bind(("127.0.0.1", 0))
                        api_url = f"http://127.0.0.1:{sock.getsockname()[1]}"
                        server = uvicorn.Server(
                            uvicorn.Config(
                                app,
                                log_level="error",
                                access_log=False,
                                host="127.0.0.1",
                                port=0,
                            )
                        )
                        thread = threading.Thread(
                            target=server.run, kwargs={"sockets": [sock]}, daemon=True
                        )
                        thread.start()
                        deadline = time.monotonic() + 15
                        while (
                            not server.started
                            and thread.is_alive()
                            and time.monotonic() < deadline
                        ):
                            time.sleep(0.05)
                        if not server.started:
                            raise RuntimeError("Servidor E2E não iniciou.")
                        try:
                            env = {
                                **os.environ,
                                "ACADEMIA_E2E_ORIGIN": origin,
                                "ACADEMIA_E2E_API": api_url,
                                "ACADEMIA_E2E_FIXTURE": str(fixtures),
                                "ACADEMIA_E2E_PASSWORD": password,
                                "ACADEMIA_E2E_CHANNEL": args.channel,
                                "ACADEMIA_E2E_OUTPUT": str(output),
                                "ACADEMIA_API_PROXY_TARGET": api_url,
                                "VITE_API_BASE_URL": "/api",
                            }
                            env.pop("GROQ_API_KEY", None)
                            node = Path(args.node).resolve()
                            env["PATH"] = (
                                str(node.parent) + os.pathsep + env.get("PATH", "")
                            )
                            command_line = [
                                str(node),
                                "node_modules/@playwright/test/cli.js",
                                "test",
                                "--config",
                                "tests/e2e/playwright.config.ts",
                            ]
                            with (output / "navegador-privado.log").open("wb") as log:
                                run = subprocess.run(
                                    command_line,
                                    cwd=ROOT / "frontend",
                                    env=env,
                                    stdout=log,
                                    stderr=subprocess.STDOUT,
                                )
                        finally:
                            server.should_exit = True
                            thread.join(timeout=15)
                            if thread.is_alive():
                                raise RuntimeError(
                                    "Servidor E2E não encerrou; preservar transação."
                                )
                        raw = json.loads(
                            (output / "playwright.json").read_text("utf-8")
                        )
                        rows = browser_rows(raw)
                        report.update(
                            casos=rows,
                            codigo_navegador=run.returncode,
                            chamadas_llm_controlado=len(ai.model.calls),
                            chamadas_llm_externo=0,
                            testes_locais_aprovados=run.returncode == 0
                            and local_acceptance(rows),
                        )
                        with sessions.begin() as session:
                            report["persistencia"] = {
                                "versoes": session.scalar(
                                    select(func.count()).select_from(WorkoutVersion)
                                ),
                                "auditorias": session.scalar(
                                    select(func.count()).select_from(AuditRecord)
                                ),
                                "avisos": session.scalar(
                                    select(func.count()).select_from(Notification)
                                ),
                            }
                finally:
                    ai.close()
            finally:
                transaction.rollback()
        with engine.connect() as clean:
            report["rollback_confirmado"] = (
                clean.scalar(text("SELECT to_regnamespace('academia')")) is None
            )
    except Exception as error:
        report.update(estado="FALHA", erro_tipo=type(error).__name__)
        write_json(output / "relatorio.json", report)
        print("FALHA: consultar relatório e logs privados locais.")
        return 1
    finally:
        engine.dispose()
    report["estado"] = (
        "LOCAL_APROVADO_ACEITE_REAL_PENDENTE"
        if report["testes_locais_aprovados"] and report["rollback_confirmado"]
        else "FALHA"
    )
    # Mesmo que AI-06 mude depois, estes doubles não autorizam o aceite integral.
    report["aceite_mvp"] = False
    write_json(output / "relatorio.json", report)
    print(report["estado"])
    return 0 if report["estado"] != "FALHA" else 1


if __name__ == "__main__":
    raise SystemExit(main())

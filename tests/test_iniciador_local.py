"""Guardas de configuração e ciclo de vida do iniciador, sem abrir serviços reais."""

import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "academia_launcher_test", ROOT / "scripts/academia_local.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def prepared(
    launcher: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Any:
    root = tmp_path / "Projeto com espaços e acento ç"
    (root / "frontend/node_modules/vite/bin").mkdir(parents=True)
    (root / "backend/.venv/Scripts").mkdir(parents=True)
    for name in ("node.exe", "mailpit.exe", "pg/bin/pg_ctl.exe", "pg/data/PG_VERSION"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    (root / "backend/.venv/Scripts/python.exe").touch()
    (root / "frontend/node_modules/vite/bin/vite.js").touch()
    (root / ".env.example").write_text(
        "ACADEMIA_AUTH_ORIGIN=http://127.0.0.1:5173\n"
        "ACADEMIA_SMTP_HOST=127.0.0.1\nACADEMIA_SMTP_PORT=1025\n",
        encoding="utf8",
    )
    (root / ".env").write_text(
        "ACADEMIA_DATABASE_URL=postgresql+psycopg://teste@127.0.0.1/academia_dev\n"
        "GROQ_API_KEY=credencial-sintetica-nao-encaminhar\n"
        "GEMINI_API_KEY=outra-credencial-sintetica\n",
        encoding="utf8",
    )
    (root / "frontend/.env.example").write_text(
        "VITE_API_BASE_URL=/api\n"
        "ACADEMIA_API_PROXY_TARGET=http://127.0.0.1:8000\n"
        "VITE_TEST_MAILBOX_URL=http://127.0.0.1:8025\n",
        encoding="utf8",
    )
    (root / "iniciador.local.json").write_text(
        json.dumps(
            {
                "node_exe": str(root / "node.exe"),
                "mailpit_exe": str(root / "mailpit.exe"),
                "postgres_bin": str(root / "pg/bin"),
                "postgres_data": str(root / "pg/data"),
            }
        ),
        encoding="utf8",
    )
    original_run = launcher.subprocess.run

    def node_version(args: list[str], **kwargs: Any) -> Any:
        if args == [str(root / "node.exe"), "--version"]:
            return SimpleNamespace(returncode=0, stdout=b"v24.22.1")
        return original_run(args, **kwargs)

    monkeypatch.setattr(launcher.subprocess, "run", node_version)
    controller = launcher.Controller(root)
    controller.configure()
    return controller


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:5173",
        "http://0.0.0.0:5173",
        "http://example.test:5173",
        "http://127.0.0.1:5173/area",
        "http://senha@127.0.0.1:5173",
        "http://127.0.0.1:5173?x=1",
    ],
)
def test_remote_or_ambiguous_addresses_are_rejected(
    launcher: ModuleType, url: str
) -> None:
    with pytest.raises(launcher.LaunchError):
        launcher.local_url(url)


def test_backend_secrets_stay_out_of_frontend_environment(prepared: Any) -> None:
    assert prepared.backend_env["GROQ_API_KEY"]
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "ACADEMIA_DATABASE_URL"):
        assert key not in prepared.frontend_env
    assert prepared.frontend_env["ACADEMIA_API_PROXY_TARGET"].endswith(":8000")


def test_occupied_port_does_not_kill_or_start_any_process(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr(launcher, "is_open", lambda port: port == 5173)
    monkeypatch.setattr(prepared, "command", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(launcher.LaunchError, match="já está em uso"):
        prepared.start()
    assert calls == [] and not prepared.processes


def test_start_rejects_postgres_address_override(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    with (prepared.root / ".env").open("a", encoding="utf-8") as source:
        source.write(
            "ACADEMIA_DATABASE_URL="
            "postgresql+psycopg://teste@127.0.0.1/academia_dev?host=example.test\n"
        )
    calls = []
    monkeypatch.setattr(launcher, "is_open", lambda port: False)
    monkeypatch.setattr(prepared, "command", lambda *args, **kwargs: calls.append(args))

    with pytest.raises(launcher.LaunchError, match="academia_dev local"):
        prepared.start()
    assert calls == []


def test_database_check_refuses_postgres_listening_on_all_addresses(
    launcher: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "backend"))
    from app.database import connection

    def listen_addresses(statement: Any) -> str:
        assert statement.text == "SHOW listen_addresses"
        return "*"

    engine = SimpleNamespace(
        connect=lambda: nullcontext(SimpleNamespace(scalar=listen_addresses)),
        dispose=lambda: None,
    )
    monkeypatch.setattr(connection, "create_database_engine", lambda target: engine)

    with pytest.raises(launcher.LaunchError, match="somente em loopback"):
        launcher.check_database()


def test_failed_database_check_sanitizes_diagnostic(
    launcher: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "backend"))
    from app.database import connection
    from sqlalchemy.exc import OperationalError

    def unavailable(target: str) -> None:
        raise OperationalError(None, None, Exception("valor privado de teste"))

    monkeypatch.setattr(connection, "create_database_engine", unavailable)
    monkeypatch.setattr(launcher.sys, "argv", ["academia_local.py", "--check-database"])

    with pytest.raises(SystemExit) as failure:
        launcher.main()
    assert failure.value.code == "Não foi possível verificar o PostgreSQL local."
    assert "valor privado" not in capsys.readouterr().err


class ProcessDouble:
    def __init__(self) -> None:
        self.pid = 12345
        self.code: int | None = None
        self.terminated = False

    def poll(self) -> int | None:
        return self.code

    def terminate(self) -> None:
        self.terminated = True
        self.code = 0

    def wait(self, timeout: int) -> int:
        self.code = 0
        return 0


def test_stop_uses_owned_handles_and_graceful_api_signal(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend, node = ProcessDouble(), ProcessDouble()
    prepared.processes = {"backend": backend, "frontend": node}
    prepared.running = True
    prepared.stop()
    assert prepared.stop_file.is_file()
    assert not backend.terminated and node.terminated
    assert not prepared.processes and not prepared.running
    assert prepared.postgres_pid is None
    prepared.stop()


def test_changed_postgres_pid_is_never_stopped(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    pid_file = Path(prepared.config["postgres_data"]) / "postmaster.pid"
    pid_file.write_text("222\n", encoding="utf8")
    prepared.postgres_pid = 111
    calls = []
    monkeypatch.setattr(prepared, "command", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(launcher.LaunchError, match="PostgreSQL"):
        prepared.stop()
    assert calls == [] and pid_file.read_text("utf8").startswith("222")


def test_failed_start_cleans_owned_services_but_keeps_existing_database(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    started: list[ProcessDouble] = []
    monkeypatch.setattr(launcher, "is_open", lambda port: port == 5432)
    monkeypatch.setattr(prepared, "verify_database", lambda: None)

    def command(name: str, args: list[str], **kwargs: object) -> None:
        proc = ProcessDouble()
        started.append(proc)
        prepared.processes[name] = proc

    def fail(*args: object, **kwargs: object) -> None:
        raise launcher.LaunchError("Falha sintética de prontidão")

    monkeypatch.setattr(prepared, "command", command)
    monkeypatch.setattr(prepared, "wait_ready", fail)
    with pytest.raises(launcher.LaunchError, match="Falha sintética"):
        prepared.start()
    assert len(started) == 1 and started[0].terminated
    assert not prepared.processes and prepared.postgres_pid is None


def test_spawn_does_not_put_credentials_on_command_line_and_clears_mailpit_relay(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def popen(args: list[str], **kwargs: Any) -> ProcessDouble:
        calls.append((args, kwargs))
        return ProcessDouble()

    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    prepared.frontend_env["MP_SMTP_RELAY_CONFIG"] = "configuracao-sintetica"
    for name in ("frontend", "backend", "mailpit"):
        prepared.command(name, ["programa com espaços.exe", "argumento"])
    assert all("credencial" not in " ".join(args) for args, _ in calls)
    assert calls[1][1]["env"]["GROQ_API_KEY"]
    assert "GROQ_API_KEY" not in calls[0][1]["env"]
    assert "MP_SMTP_RELAY_CONFIG" not in calls[2][1]["env"]
    assert all(not kwargs.get("shell", False) for _, kwargs in calls)


def test_postgres_management_only_passes_app_secrets_to_readiness_probe(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    environments = []

    def run(args: list[str], *, env: dict[str, str], **kwargs: Any) -> Any:
        environments.append(env)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    for command in ("postgres", "verificar-banco", "postgres-encerrar"):
        prepared.command(command, ["programa.exe"], wait=True)
    for key in ("ACADEMIA_DATABASE_URL", "GROQ_API_KEY"):
        assert [key in env for env in environments] == [False, True, False]


def enable_turnstile(prepared: Any, port: int = 8011) -> None:
    with (prepared.root / ".env").open("a", encoding="utf-8") as source:
        source.write(
            f"ACADEMIA_TURNSTILE_URL=http://127.0.0.1:{port}\n"
            "ACADEMIA_TURNSTILE_COMMAND_TOKEN=teste_sintetico_comando_1234567890\n"
            "ACADEMIA_TURNSTILE_CALLBACK_TOKEN=teste_sintetico_retorno_1234567890\n"
        )


def test_turnstile_has_separate_environment_and_uses_project_root(
    launcher: ModuleType, prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_turnstile(prepared)
    prepared.configure()
    assert prepared.turnstile_port == 8011
    env = prepared.turnstile_env
    assert env["ACADEMIA_TURNSTILE_CALLBACK_URL"] == (
        prepared.api + "/api/v1/acesso/catraca/passagens"
    )
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "ACADEMIA_DATABASE_URL"):
        assert key not in env
    for key in (
        "ACADEMIA_TURNSTILE_COMMAND_TOKEN",
        "ACADEMIA_TURNSTILE_CALLBACK_TOKEN",
    ):
        assert key in env and key not in prepared.frontend_env

    calls: list[dict[str, Any]] = []

    def popen(args: list[str], **kwargs: Any) -> ProcessDouble:
        calls.append(kwargs)
        return ProcessDouble()

    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    prepared.command("turnstile", ["python", "-m", "simulators.turnstile"])
    assert calls[0]["cwd"] == prepared.root
    assert calls[0]["env"] == env
    simulator = prepared.processes["turnstile"]
    prepared.stop()
    assert simulator.terminated and not prepared.processes


def test_turnstile_port_collision_is_rejected(
    launcher: ModuleType, prepared: Any
) -> None:
    enable_turnstile(prepared, port=8000)
    with pytest.raises(launcher.LaunchError, match="porta da catraca"):
        prepared.configure()


def test_stop_without_panel_does_not_leave_a_delayed_shutdown(
    launcher: ModuleType, tmp_path: Path
) -> None:
    assert not launcher.request_stop(tmp_path)
    assert not (tmp_path / "backend/data/iniciador/painel-encerrar").exists()


def test_stop_command_signals_only_the_running_project_panel(
    launcher: ModuleType, tmp_path: Path
) -> None:
    import portalocker

    runtime = tmp_path / "backend/data/iniciador"
    runtime.mkdir(parents=True)
    with portalocker.Lock(str(runtime / "painel.lock"), timeout=0):
        assert launcher.request_stop(tmp_path)
        assert (runtime / "painel-encerrar").is_file()

"""Painel Windows para ligar/desligar o ambiente local já preparado do AcademIA."""

from __future__ import annotations

import argparse
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


class LaunchError(Exception):
    """Mensagem segura para o painel; detalhes técnicos ficam em logs privados."""


def is_open(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def local_url(value: str) -> tuple[str, int]:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise LaunchError(
            "O iniciador aceita somente endereços HTTP locais em 127.0.0.1."
        )
    return value.rstrip("/"), parsed.port


def read_env(path: Path) -> dict[str, str]:
    return {
        key: value for key, value in dotenv_values(path).items() if value is not None
    }


class Controller:
    def __init__(self, root: Path, notify: Callable[[str], None] = lambda _: None):
        self.root = root.resolve()
        self.runtime = self.root / "backend/data/iniciador"
        self.notify = notify
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        self.postgres_pid: int | None = None
        self.running = False
        self.backend_env: dict[str, str] = {}
        self.frontend_env: dict[str, str] = {}
        self.turnstile_env: dict[str, str] = {}
        self.config: dict[str, str] = {}
        self.site = self.mailbox = self.api = self.turnstile = ""
        self.turnstile_port: int | None = None
        self.stop_file = self.runtime / "api-encerrar"

    def configure(self) -> None:
        if not (self.root / ".env").is_file():
            raise LaunchError("Falta o .env local. Consulte o guia de inicialização.")
        defaults = read_env(self.root / ".env.example")
        self.backend_env = {**os.environ, **defaults, **read_env(self.root / ".env")}
        # Segredos do backend não são repassados ao Vite ou ao Mailpit.
        public_env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith(("ACADEMIA_", "GROQ_", "GEMINI_", "MP_"))
        }
        front = {
            **read_env(self.root / "frontend/.env.example"),
            **read_env(self.root / "frontend/.env.local"),
        }
        self.frontend_env = {**public_env, **front}
        if front.get("VITE_API_BASE_URL") != "/api":
            raise LaunchError(
                "Configure VITE_API_BASE_URL=/api para o iniciador local."
            )
        self.site, self.site_port = local_url(self.backend_env["ACADEMIA_AUTH_ORIGIN"])
        self.api, self.api_port = local_url(front["ACADEMIA_API_PROXY_TARGET"])
        self.mailbox, self.mail_port = local_url(front["VITE_TEST_MAILBOX_URL"])
        if self.backend_env.get("ACADEMIA_SMTP_HOST") != "127.0.0.1":
            raise LaunchError("O SMTP precisa apontar ao Mailpit local (127.0.0.1).")
        self.smtp_port = int(self.backend_env["ACADEMIA_SMTP_PORT"])
        if not 1024 <= self.smtp_port <= 65535:
            raise LaunchError("A porta SMTP precisa estar entre 1024 e 65535.")
        if len({self.site_port, self.api_port, self.mail_port, self.smtp_port}) != 4:
            raise LaunchError(
                "As portas do frontend, API e Mailpit precisam ser distintas."
            )
        self.turnstile_port = None
        self.turnstile = ""
        self.turnstile_env = {}
        prefix = "ACADEMIA_TURNSTILE_"
        command_token = self.backend_env.get(prefix + "COMMAND_TOKEN")
        callback_token = self.backend_env.get(prefix + "CALLBACK_TOKEN")
        if command_token or callback_token:
            if (
                not command_token
                or not callback_token
                or command_token == callback_token
            ):
                raise LaunchError(
                    "Configure dois tokens distintos para a catraca fictícia."
                )
            self.turnstile, self.turnstile_port = local_url(
                self.backend_env.get(prefix + "URL", "http://127.0.0.1:8011")
            )
            if self.turnstile_port in {
                self.site_port,
                self.api_port,
                self.mail_port,
                self.smtp_port,
            }:
                raise LaunchError("A porta da catraca precisa ser distinta.")
            self.turnstile_env = {
                **public_env,
                **{k: v for k, v in self.backend_env.items() if k.startswith(prefix)},
            }
            if not self.turnstile_env.get(prefix + "CALLBACK_URL"):
                self.turnstile_env[prefix + "CALLBACK_URL"] = (
                    self.api + "/api/v1/acesso/catraca/passagens"
                )
        config_file = self.root / "iniciador.local.json"
        if not config_file.is_file():
            raise LaunchError(
                "Falta iniciador.local.json com os caminhos das ferramentas. "
                "Consulte docs/instalacao/iniciar-com-dois-cliques.md."
            )
        config = json.loads(config_file.read_text("utf-8-sig"))
        if not isinstance(config, dict) or any(
            not isinstance(v, str) for v in config.values()
        ):
            raise LaunchError("O arquivo iniciador.local.json está inválido.")
        self.config = config
        for key in ("postgres_bin", "postgres_data", "mailpit_exe", "node_exe"):
            if not config.get(key):
                raise LaunchError(f"Falta o caminho {key} em iniciador.local.json.")
        for path in (
            self.python,
            self.pg_ctl,
            Path(config["postgres_data"]) / "PG_VERSION",
            Path(config["mailpit_exe"]),
            Path(config["node_exe"]),
            self.root / "frontend/node_modules/vite/bin/vite.js",
        ):
            if not path.is_file():
                raise LaunchError(f"Recurso local não encontrado: {path}")
        result = subprocess.run(
            [config["node_exe"], "--version"],
            capture_output=True,
            creationflags=HIDDEN,
            timeout=10,
            check=False,
        )
        if result.returncode or not result.stdout.startswith(b"v24."):
            raise LaunchError("O projeto precisa do Node 24 já instalado.")

    @property
    def python(self) -> Path:
        return self.root / "backend/.venv/Scripts/python.exe"

    @property
    def pg_ctl(self) -> Path:
        return Path(self.config["postgres_bin"]) / "pg_ctl.exe"

    def command(self, name: str, args: list[str], *, wait: bool = False) -> None:
        self.runtime.mkdir(parents=True, exist_ok=True)
        with (self.runtime / f"{name}.log").open("ab") as log:
            if wait:
                result = subprocess.run(
                    args,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=self.backend_env,
                    creationflags=HIDDEN,
                    timeout=50,
                    check=False,
                )
                if result.returncode:
                    raise LaunchError(f"Falha em {name}. Use o botão Abrir registros.")
            else:
                env = self.backend_env if name == "backend" else self.frontend_env
                if name == "turnstile":
                    env = self.turnstile_env
                if name == "mailpit":
                    env = {k: v for k, v in env.items() if not k.startswith("MP_")}
                working_dirs = {
                    "frontend": self.root / "frontend",
                    "turnstile": self.root,
                }
                cwd = working_dirs.get(name, self.root / "backend")
                self.processes[name] = subprocess.Popen(
                    args,
                    cwd=cwd,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=HIDDEN,
                )

    def wait_ready(self, name: str, url: str, *, health: bool = False) -> None:
        opener = build_opener(ProxyHandler({}))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            proc = self.processes.get(name)
            if proc and proc.poll() is not None:
                raise LaunchError(f"O serviço {name} parou. Use Abrir registros.")
            try:
                with opener.open(url, timeout=1) as response:
                    if response.status == 200 and (
                        not health or json.load(response) == {"status": "ok"}
                    ):
                        return
            except (OSError, ValueError):
                pass
            time.sleep(0.2)
        raise LaunchError(f"O serviço {name} não ficou pronto. Use Abrir registros.")

    def verify_database(self) -> None:
        # O subprocesso usa a configuração privada sem colocá-la na linha de comando.
        self.command(
            "verificar-banco",
            [
                str(self.python),
                str(Path(__file__).resolve()),
                "--check-database",
                "--project-root",
                str(self.root),
            ],
            wait=True,
        )

    def start(self) -> None:
        if self.running:
            return
        self.configure()
        ports = [self.site_port, self.api_port, self.mail_port, self.smtp_port]
        if self.turnstile_port is not None:
            ports.append(self.turnstile_port)
        for port in ports:
            if is_open(port):
                raise LaunchError(
                    f"A porta {port} já está em uso. Feche a execução anterior; "
                    "o iniciador não encerra processos de outros programas."
                )
        try:
            self.notify("Iniciando o banco de dados…")
            from sqlalchemy import make_url

            url = make_url(self.backend_env["ACADEMIA_DATABASE_URL"])
            if url.database != "academia_dev" or url.host != "127.0.0.1":
                raise LaunchError("O iniciador exige o banco academia_dev local.")
            if not is_open(url.port or 5432):
                self.command(
                    "postgres",
                    [
                        str(self.pg_ctl),
                        "-D",
                        self.config["postgres_data"],
                        "-l",
                        str(self.runtime / "postgres-servidor.log"),
                        "-w",
                        "start",
                    ],
                    wait=True,
                )
                self.postgres_pid = int(
                    (Path(self.config["postgres_data"]) / "postmaster.pid")
                    .read_text()
                    .splitlines()[0]
                )
            self.verify_database()
            self.notify("Abrindo a caixa local de e-mails…")
            self.command(
                "mailpit",
                [
                    self.config["mailpit_exe"],
                    "--listen",
                    f"127.0.0.1:{self.mail_port}",
                    "--smtp",
                    f"127.0.0.1:{self.smtp_port}",
                    "--disable-version-check",
                    "--ignore-duplicate-ids",
                    "--max",
                    "0",
                    "--database",
                    str(self.root / "backend/data/mailpit.db"),
                ],
            )
            self.wait_ready("mailpit", self.mailbox + "/api/v1/info")
            self.notify("Iniciando a API…")
            self.stop_file.unlink(missing_ok=True)
            self.command(
                "backend",
                [
                    str(self.python),
                    str(Path(__file__).resolve()),
                    "--api",
                    "--stop-file",
                    str(self.stop_file),
                    "--project-root",
                    str(self.root),
                ],
            )
            self.wait_ready("backend", self.api + "/health", health=True)
            if self.turnstile_port is not None:
                self.notify("Iniciando a catraca fictícia…")
                self.command(
                    "turnstile", [str(self.python), "-m", "simulators.turnstile"]
                )
                self.wait_ready("turnstile", self.turnstile + "/health", health=True)
            self.notify("Iniciando o site…")
            self.command(
                "frontend",
                [
                    self.config["node_exe"],
                    "node_modules/vite/bin/vite.js",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(self.site_port),
                    "--strictPort",
                ],
            )
            self.wait_ready("frontend", self.site + "/api/health", health=True)
            self.running = True
            self.notify("Sistema pronto. O site já pode ser usado.")
        except Exception:
            self.stop()
            raise

    def stop(self) -> None:
        self.notify("Encerrando os serviços iniciados por este painel…")
        errors = []
        for name in ("frontend", "turnstile", "backend", "mailpit"):
            proc = self.processes.get(name)
            if proc is None:
                continue
            try:
                if proc.poll() is None:
                    if name == "backend":
                        self.stop_file.parent.mkdir(parents=True, exist_ok=True)
                        self.stop_file.touch()
                        try:
                            proc.wait(timeout=25)
                        except subprocess.TimeoutExpired:
                            # Apenas a árvore do processo que este painel criou.
                            subprocess.run(
                                ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
                                capture_output=True,
                                creationflags=HIDDEN,
                                timeout=10,
                                check=True,
                            )
                    else:
                        proc.terminate()
                    proc.wait(timeout=10)
                del self.processes[name]
            except (OSError, subprocess.SubprocessError):
                errors.append(name)
        if self.postgres_pid is not None:
            pid_file = Path(self.config["postgres_data"]) / "postmaster.pid"
            try:
                if pid_file.exists():
                    if int(pid_file.read_text().splitlines()[0]) != self.postgres_pid:
                        raise LaunchError("O banco foi reiniciado por outro processo.")
                    self.command(
                        "postgres-encerrar",
                        [
                            str(self.pg_ctl),
                            "-D",
                            self.config["postgres_data"],
                            "-m",
                            "fast",
                            "-w",
                            "stop",
                        ],
                        wait=True,
                    )
                self.postgres_pid = None
            except (OSError, ValueError, LaunchError, subprocess.SubprocessError):
                errors.append("PostgreSQL")
        self.running = False
        if errors:
            raise LaunchError("Não foi possível encerrar: " + ", ".join(errors))
        self.notify("Sistema encerrado. Seus dados foram preservados.")


def check_database() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from app.database.connection import create_database_engine

    engine = create_database_engine("dev")
    try:
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_heads()
            expected = ScriptDirectory.from_config(
                Config(str(ROOT / "database/alembic.ini"))
            ).get_heads()
            if set(current) != set(expected):
                raise LaunchError(
                    "Migrations pendentes; procure o responsável técnico."
                )
    finally:
        engine.dispose()


def run_api(stop_file: Path) -> None:
    os.chdir(ROOT / "backend")
    sys.path.insert(0, str(ROOT / "backend"))
    import uvicorn

    front = {
        **read_env(ROOT / "frontend/.env.example"),
        **read_env(ROOT / "frontend/.env.local"),
    }
    _, port = local_url(front["ACADEMIA_API_PROXY_TARGET"])
    server = uvicorn.Server(
        uvicorn.Config(
            "app.main:create_app",
            factory=True,
            host="127.0.0.1",
            port=port,
            workers=1,
            access_log=False,
            timeout_graceful_shutdown=15,
        )
    )

    def watch() -> None:
        while not stop_file.exists():
            time.sleep(0.2)
        server.should_exit = True

    threading.Thread(target=watch, daemon=True).start()
    server.run()


def panel(open_browser: bool = True) -> None:
    if os.name == "nt":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "AcademIA.IniciadorLocal"
        )
    import tkinter as tk
    from tkinter import messagebox, ttk

    import portalocker

    runtime = ROOT / "backend/data/iniciador"
    runtime.mkdir(parents=True, exist_ok=True)
    lock = portalocker.Lock(str(runtime / "painel.lock"), timeout=0)
    try:
        lock.acquire()
    except portalocker.exceptions.LockException:
        messagebox.showinfo(
            "AcademIA", "O painel já está aberto. Use a janela existente."
        )
        return
    shutdown_request = runtime / "painel-encerrar"
    shutdown_request.unlink(missing_ok=True)
    window = tk.Tk()
    window.title("AcademIA — iniciar e testar")
    window.geometry("610x405")
    window.minsize(580, 380)
    window.configure(background="#f3f7f6")
    messages: queue.Queue[tuple[str, str]] = queue.Queue()
    controller = Controller(ROOT, lambda text: messages.put(("status", text)))
    status = tk.StringVar(value="Preparando a inicialização…")
    busy = False
    closing = False
    box = ttk.Frame(window, padding=24)
    box.pack(fill="both", expand=True)
    ttk.Label(box, text="AcademIA", font=("Segoe UI", 24, "bold")).pack(anchor="w")
    ttk.Label(
        box, text="Ambiente local para testes manuais", font=("Segoe UI", 12)
    ).pack(anchor="w", pady=(0, 20))
    ttk.Label(box, textvariable=status, wraplength=520).pack(anchor="w", pady=(0, 16))
    buttons = ttk.Frame(box)
    buttons.pack(fill="x")

    def work(start: bool) -> None:
        nonlocal busy
        if busy:
            return
        busy = True
        start_button.configure(state="disabled")
        stop_button.configure(state="disabled")

        def execute() -> None:
            try:
                controller.start() if start else controller.stop()
                messages.put(("started" if start else "stopped", ""))
            except Exception as error:
                safe = (
                    str(error)
                    if isinstance(error, LaunchError)
                    else (
                        "Não foi possível concluir. "
                        "Confira a configuração e os registros."
                    )
                )
                messages.put(("error", safe))

        threading.Thread(target=execute, daemon=True).start()

    start_button = ttk.Button(
        buttons, text="Iniciar sistema", command=lambda: work(True)
    )
    start_button.grid(row=0, column=0, padx=(0, 8), pady=4)
    site_button = ttk.Button(
        buttons,
        text="Abrir site",
        state="disabled",
        command=lambda: webbrowser.open(controller.site),
    )
    site_button.grid(row=0, column=1, padx=8, pady=4)
    mail_button = ttk.Button(
        buttons,
        text="Abrir e-mails de teste",
        state="disabled",
        command=lambda: webbrowser.open(controller.mailbox),
    )
    mail_button.grid(row=1, column=0, padx=(0, 8), pady=4)
    stop_button = ttk.Button(
        buttons, text="Encerrar sistema", state="disabled", command=lambda: work(False)
    )
    stop_button.grid(row=1, column=1, padx=8, pady=4)
    ttk.Button(box, text="Abrir registros", command=lambda: os.startfile(runtime)).pack(
        anchor="w", pady=(12, 6)
    )
    ttk.Label(
        box,
        text="Os e-mails ficam na caixa local, não no Gmail.\n"
        "Fechar este painel encerra os serviços que ele iniciou.",
        wraplength=520,
    ).pack(anchor="w")

    def poll() -> None:
        nonlocal busy
        while not messages.empty():
            kind, text = messages.get_nowait()
            if kind == "status":
                status.set(text)
                continue
            busy = False
            active = bool(controller.processes) or controller.postgres_pid is not None
            start_button.configure(state="disabled" if active else "normal")
            stop_button.configure(state="normal" if active else "disabled")
            for button in (site_button, mail_button):
                button.configure(state="normal" if controller.running else "disabled")
            if kind == "started" and open_browser:
                webbrowser.open(controller.site)
            if kind == "error":
                status.set(text)
                messagebox.showerror("AcademIA — atenção", text)
            if closing and kind == "stopped":
                window.destroy()
                return
        if shutdown_request.exists() and not busy:
            shutdown_request.unlink()
            if close():
                return
        window.after(120, poll)

    def close() -> bool:
        nonlocal closing
        if busy:
            messagebox.showinfo(
                "AcademIA", "Aguarde a operação terminar antes de fechar."
            )
        elif controller.running or controller.processes or controller.postgres_pid:
            closing = True
            work(False)
        else:
            window.destroy()
            return True
        return False

    window.protocol("WM_DELETE_WINDOW", close)
    window.after(120, poll)
    window.after(200, lambda: work(True))
    try:
        window.mainloop()
    finally:
        lock.release()


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", action="store_true")
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--check-database", action="store_true")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.project_root:
        ROOT = args.project_root.resolve()
    if args.stop:
        request_stop(ROOT)
    elif args.api:
        if args.stop_file is None:
            parser.error("Falta stop-file.")
        run_api(args.stop_file)
    elif args.check_database:
        check_database()
    else:
        panel(open_browser=not args.no_browser)


def request_stop(root: Path) -> bool:
    import portalocker

    runtime = root / "backend/data/iniciador"
    runtime.mkdir(parents=True, exist_ok=True)
    lock = portalocker.Lock(str(runtime / "painel.lock"), timeout=0)
    try:
        lock.acquire()
    except portalocker.exceptions.LockException:
        (runtime / "painel-encerrar").touch()
        return True
    else:
        lock.release()
        return False


if __name__ == "__main__":
    main()

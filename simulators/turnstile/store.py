from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection, connect
from uuid import UUID

from simulators.turnstile.contracts import Command, Passage


class RejectedOperation(Exception):
    def __init__(self, status: int, code: str) -> None:
        self.status = status
        self.code = code


_SCHEMA_VERSION = 1
_DDL = """
CREATE TABLE IF NOT EXISTS commands (
    request_id TEXT PRIMARY KEY,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS passages (
    event_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE REFERENCES commands(request_id),
    body TEXT NOT NULL,
    confirmed INTEGER NOT NULL DEFAULT 0 CHECK (confirmed IN (0, 1))
);
"""


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def prepare(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect(create=True) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == _SCHEMA_VERSION:
                return
            if (
                version != 0
                or db.execute(
                    "SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchone()
            ):
                raise ValueError("O arquivo informado não pertence à catraca fictícia.")
            db.executescript(
                f"BEGIN IMMEDIATE;{_DDL}PRAGMA user_version = {_SCHEMA_VERSION};COMMIT;"
            )

    def verify(self) -> None:
        with self._connect() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != _SCHEMA_VERSION:
                raise ValueError("Prepare o armazenamento local da catraca.")
            db.execute("SELECT body FROM commands LIMIT 0")
            db.execute("SELECT confirmed FROM passages LIMIT 0")

    @contextmanager
    def _connect(self, *, create: bool = False) -> Iterator[Connection]:
        db = connect(
            self.path.as_uri() + ("?mode=rwc" if create else "?mode=rw"), uri=True
        )
        try:
            db.execute("PRAGMA foreign_keys = ON")
            yield db
        finally:
            db.close()

    @contextmanager
    def _write(self) -> Iterator[Connection]:
        with self._connect() as db, db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    def accept(self, command: Command, now: datetime) -> bool:
        key = str(command.request_id)
        payload = command.model_dump_json()
        with self._write() as db:
            prior = db.execute(
                "SELECT body FROM commands WHERE request_id = ?", (key,)
            ).fetchone()
            if prior is not None:
                if prior[0] != payload:
                    raise RejectedOperation(409, "COMMAND_CONFLICT")
                return False
            if command.expires_at <= now:
                raise RejectedOperation(410, "COMMAND_EXPIRED")
            db.execute("INSERT INTO commands VALUES (?, ?)", (key, payload))
            return True

    def reserve_passage(
        self, request_id: UUID, event_id: UUID, now: datetime
    ) -> tuple[Passage, bool]:
        request = str(request_id)
        event = str(event_id)
        with self._write() as db:
            command_row = db.execute(
                "SELECT body FROM commands WHERE request_id = ?", (request,)
            ).fetchone()
            if command_row is None:
                raise RejectedOperation(404, "COMMAND_NOT_FOUND")
            prior = db.execute(
                "SELECT event_id, body, confirmed FROM passages WHERE request_id = ?",
                (request,),
            ).fetchone()
            if prior is not None:
                if prior[0] != event:
                    raise RejectedOperation(409, "PASSAGE_CONFLICT")
                return Passage.model_validate_json(prior[1]), bool(prior[2])
            if db.execute(
                "SELECT 1 FROM passages WHERE event_id = ?", (event,)
            ).fetchone():
                raise RejectedOperation(409, "PASSAGE_CONFLICT")
            command = Command.model_validate_json(command_row[0])
            if command.decision == "DENY":
                raise RejectedOperation(409, "COMMAND_DENIED")
            if now >= command.expires_at:
                raise RejectedOperation(410, "COMMAND_EXPIRED")
            passage = Passage(
                schema_version=1,
                event_id=event_id,
                request_id=request_id,
                occurred_at=now,
                direction=command.direction,
            )
            db.execute(
                "INSERT INTO passages (event_id, request_id, body) VALUES (?, ?, ?)",
                (event, request, passage.model_dump_json()),
            )
            return passage, False

    def confirm(self, event_id: UUID) -> bool:
        with self._write() as db:
            return (
                db.execute(
                    "UPDATE passages SET confirmed = 1 "
                    "WHERE event_id = ? AND confirmed = 0",
                    (str(event_id),),
                ).rowcount
                == 1
            )

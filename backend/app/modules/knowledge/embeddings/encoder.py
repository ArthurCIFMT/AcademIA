import json
import math
import os
import queue
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from threading import RLock, Thread
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from tokenizers import Tokenizer

from app.modules.knowledge.embeddings.provision import verify
from app.modules.knowledge.embeddings.settings import EmbeddingSettings
from app.modules.knowledge.vector.contracts import EmbeddingSpace


class EmbeddingError(Exception):
    def __init__(self, code: str, *, transient: bool = False) -> None:
        self.code, self.transient = code, transient
        super().__init__(code)


class Encoder(Protocol):
    @property
    def space(self) -> EmbeddingSpace: ...
    def tokens(self, text: str) -> int: ...
    def passages(self, texts: Sequence[str], timeout: float) -> list[list[float]]: ...


def validate_vectors(vectors: list[list[float]], count: int, dimension: int) -> None:
    if len(vectors) != count or any(
        len(v) != dimension
        or any(not math.isfinite(x) for x in v)
        or abs(math.sqrt(math.fsum(x * x for x in v)) - 1) > 0.001
        for v in vectors
    ):
        raise EmbeddingError("VETORES_INVALIDOS")


class E5Encoder:
    def __init__(self, settings: EmbeddingSettings | None = None) -> None:
        self.settings = settings or EmbeddingSettings()
        self._tokenizer: Tokenizer | None = None
        self._root: Path | None = None
        self._process: subprocess.Popen[bytes] | None = None
        self._responses: queue.Queue[bytes | None] = queue.Queue()
        self._lock = RLock()

    @property
    def space(self) -> EmbeddingSpace:
        return EmbeddingSpace(
            model=self.settings.model, revision=self.settings.revision, dimension=384
        )

    def tokens(self, text: str) -> int:
        with self._lock:
            if self._tokenizer is None:
                try:
                    from tokenizers import Tokenizer

                    self._root = verify(self.settings, full=True)
                    self._tokenizer = Tokenizer.from_file(
                        str(self._root / "tokenizer.json")
                    )
                    self._tokenizer.no_truncation()
                    self._tokenizer.no_padding()
                except (OSError, ValueError, KeyError):
                    raise EmbeddingError("PESOS_AUSENTES_OU_INVALIDOS") from None
            return len(self._tokenizer.encode(text).ids)

    def _start(self) -> None:
        self.tokens("verificação")
        environment = {
            **os.environ,
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "TOKENIZERS_PARALLELISM": "false",
        }
        self._responses = queue.Queue()
        process = subprocess.Popen(
            [sys.executable, "-m", "app.modules.knowledge.embeddings.worker"],
            cwd=Path(__file__).resolve().parents[4],
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._process = process
        responses = self._responses

        def read() -> None:
            assert process.stdout is not None
            try:
                while line := process.stdout.readline(4194305):
                    responses.put(line)
            finally:
                responses.put(None)

        Thread(target=read, daemon=True).start()

    def passages(self, texts: Sequence[str], timeout: float) -> list[list[float]]:
        return self._encode(texts, "passage: ", timeout)

    def queries(self, texts: Sequence[str], timeout: float) -> list[list[float]]:
        return self._encode(texts, "query: ", timeout)

    def _encode(
        self, texts: Sequence[str], prefix: str, timeout: float
    ) -> list[list[float]]:
        if not texts or len(texts) > self.settings.batch_size:
            raise EmbeddingError("LOTE_INVALIDO")
        with self._lock:
            if any(
                not text.strip() or self.tokens(prefix + text) > 512 for text in texts
            ):
                raise EmbeddingError("CONTEXTO_EXCEDIDO")
            try:
                if self._process is None:
                    self._start()
                assert self._process is not None and self._process.stdin is not None
                body = {
                    "path": str(self._root),
                    "threads": self.settings.cpu_threads,
                    "texts": [prefix + text for text in texts],
                }
                self._process.stdin.write(json.dumps(body).encode() + b"\n")
                self._process.stdin.flush()
                raw = self._responses.get(timeout=timeout)
                if not raw or len(raw) > 4194304:
                    raise EmbeddingError("SERVICO_INDISPONIVEL", transient=True)
                response = json.loads(raw)
                if response.get("status") != "OK":
                    raise EmbeddingError("SERVICO_INDISPONIVEL", transient=True)
                vectors = [[float(x) for x in row] for row in response["vectors"]]
                validate_vectors(vectors, len(texts), 384)
                return vectors
            except queue.Empty:
                self.close()
                raise EmbeddingError("TIMEOUT", transient=True) from None
            except (OSError, ValueError, KeyError, TypeError):
                self.close()
                raise EmbeddingError("RESPOSTA_INVALIDA") from None
            except EmbeddingError:
                self.close()
                raise

    def close(self) -> None:
        with self._lock:
            if self._process is not None:
                process, self._process = self._process, None
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                if process.stdin:
                    process.stdin.close()
                if process.stdout:
                    process.stdout.close()

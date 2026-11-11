import hashlib
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID, uuid5

import portalocker
from pydantic import ValidationError

from app.modules.knowledge.ingestion.contracts import (
    ExtractionPolicy,
    ExtractionResult,
    ParsedDocument,
    Reason,
    State,
    digest,
)
from app.modules.knowledge.ingestion.parser import failed
from app.modules.knowledge.ingestion.process import run_parser
from app.modules.knowledge.schemas import MAX_BYTES
from app.modules.knowledge.service import ApprovedReference
from app.modules.knowledge.storage import CorpusStorage, InvalidFile

ApprovalCheck = Callable[[UUID, int], bool]
Parser = Callable[[bytes, str, str | None, ExtractionPolicy], ParsedDocument]


class ExtractionError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class Extractor:
    def __init__(
        self,
        storage: CorpusStorage,
        *,
        root: Path | None = None,
        policy: ExtractionPolicy | None = None,
        parser: Parser = run_parser,
    ) -> None:
        self.storage = storage
        self.root = (
            root or Path(os.environ.get("ACADEMIA_EXTRACTION_DIR", "data/extracoes"))
        ).resolve()
        self.policy = policy or ExtractionPolicy()
        self.parser = parser

    def _path(self, id: UUID, suffix: str) -> Path:
        target = (self.root / (id.hex + suffix)).resolve()
        if target.parent != self.root:
            raise ExtractionError("ARMAZENAMENTO_INDISPONIVEL")
        return target

    def _read(self, path: Path) -> ExtractionResult | None:
        try:
            with path.open("rb") as stream:
                content = stream.read(67108865)
        except FileNotFoundError:
            return None
        if len(content) > 67108864:
            raise ExtractionError("ARTEFATO_INCONSISTENTE")
        try:
            envelope = json.loads(content)
            if digest(envelope["resultado"]) != envelope["sha256"]:
                raise ValueError()
            return ExtractionResult.model_validate(envelope["resultado"])
        except (ValueError, KeyError, TypeError, ValidationError):
            raise ExtractionError("ARTEFATO_INCONSISTENTE") from None

    def _write(self, path: Path, result: ExtractionResult) -> None:
        payload = result.model_dump(mode="json")
        envelope = json.dumps(
            {"sha256": digest(payload), "resultado": payload}, ensure_ascii=False
        )
        encoded = envelope.encode("utf-8")
        if len(encoded) > 67108864:
            raise ExtractionError("RESULTADO_EXCEDE_LIMITE")
        temporary = None
        try:
            with NamedTemporaryFile(dir=self.root, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _content(self, reference: ApprovedReference) -> bytes | None:
        try:
            with self.storage.path(reference.reference).open("rb") as stream:
                content = stream.read(MAX_BYTES + 1)
        except (OSError, InvalidFile):
            return None
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            return None
        return content

    def extract(
        self,
        reference: ApprovedReference,
        *,
        approval_check: ApprovalCheck,
        retry_failed: bool = False,
    ) -> ExtractionResult:
        # O chamador usa a porta aprovada RAG-01 e uma checagem fresca, inclusive
        # para replay. Não manter transação SQL durante o subprocesso de parsing.
        if not approval_check(reference.version_id, reference.revision):
            raise ExtractionError("VERSAO_NAO_APROVADA")
        id = uuid5(
            reference.version_id, reference.sha256 + ":" + self.policy.fingerprint
        )
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            path = self._path(id, ".json")
            with portalocker.Lock(str(self._path(id, ".lock")), timeout=10):
                previous = self._read(path)
                if previous is not None:
                    if (
                        previous.id != id
                        or previous.documento_versao_id != reference.version_id
                        or previous.arquivo_sha256 != reference.sha256
                        or previous.aprovacao_revisao != reference.revision
                        or previous.metadados != reference.metadata
                        or previous.config_sha256 != self.policy.fingerprint
                    ):
                        raise ExtractionError("ARTEFATO_INCONSISTENTE")
                    retry = (
                        retry_failed
                        and previous.resultado.estado == State.FALHA
                        and previous.tentativa < 3
                    )
                    if not retry:
                        if not approval_check(reference.version_id, reference.revision):
                            raise ExtractionError("VERSAO_NAO_APROVADA")
                        return previous
                content = self._content(reference)
                if content is None:
                    parsed = failed(Reason.ARQUIVO_AUSENTE_OU_ALTERADO)
                else:
                    parsed = self.parser(
                        content, reference.format, reference.metadata.secao, self.policy
                    )
                # Revogação durante a extração impede gravar/entregar o resultado.
                if not approval_check(reference.version_id, reference.revision):
                    raise ExtractionError("VERSAO_NAO_APROVADA")
                history = previous.historico[:] if previous else []
                if previous:
                    history.append(
                        {
                            "estado": previous.resultado.estado.value,
                            "motivos": ",".join(
                                m.value for m in previous.resultado.motivos
                            ),
                            "criado_em": previous.criado_em.isoformat(),
                        }
                    )
                result = ExtractionResult(
                    id=id,
                    documento_versao_id=reference.version_id,
                    aprovacao_revisao=reference.revision,
                    arquivo_sha256=reference.sha256,
                    formato=reference.format,
                    metadados=reference.metadata,
                    config_sha256=self.policy.fingerprint,
                    politica=self.policy,
                    criado_em=datetime.now(UTC),
                    tentativa=previous.tentativa + 1 if previous else 1,
                    historico=history,
                    resultado=parsed,
                )
                self._write(path, result)
                return result
        except (OSError, portalocker.exceptions.LockException):
            raise ExtractionError("ARMAZENAMENTO_INDISPONIVEL") from None

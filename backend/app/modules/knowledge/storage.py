import base64
import binascii
import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.modules.knowledge.schemas import MAX_BYTES


class InvalidFile(Exception):
    pass


def validate_content(content: bytes, format: str) -> str:
    if not content or len(content) > MAX_BYTES:
        raise InvalidFile()
    if format == "PDF":
        if not content.startswith(b"%PDF-"):
            raise InvalidFile()
    elif format == "TXT":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise InvalidFile() from None
        if not text.strip() or "\x00" in text:
            raise InvalidFile()
    else:
        raise InvalidFile()
    return hashlib.sha256(content).hexdigest()


def decode_file(encoded: str, format: str) -> bytes:
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise InvalidFile() from None
    validate_content(content, format)
    return content


class CorpusStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (
            root or Path(os.environ.get("ACADEMIA_CORPUS_DIR", "data/corpus"))
        ).resolve()

    def path(self, reference: str) -> Path:
        import re

        if not re.fullmatch(r"[0-9a-f]{64}\.(pdf|txt)", reference):
            raise InvalidFile()
        target = (self.root / reference).resolve()
        if target.parent != self.root:
            raise InvalidFile()
        return target

    def store(self, content: bytes, format: str) -> tuple[str, str]:
        digest = validate_content(content, format)
        reference = digest + "." + format.lower()
        target = self.path(reference)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile(dir=self.root, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            try:
                os.link(temporary, target)
            except FileExistsError:
                if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise InvalidFile() from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return reference, digest

    def read(self, reference: str, digest: str) -> bytes:
        try:
            content = self.path(reference).read_bytes()
        except OSError:
            raise InvalidFile() from None
        if hashlib.sha256(content).hexdigest() != digest:
            raise InvalidFile()
        return content

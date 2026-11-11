import base64
import json
import subprocess
import sys

from pydantic import ValidationError

from app.modules.knowledge.ingestion.contracts import (
    ExtractionPolicy,
    ParsedDocument,
    Reason,
)
from app.modules.knowledge.ingestion.parser import failed


def run_parser(
    content: bytes, format: str, declared: str | None, policy: ExtractionPolicy
) -> ParsedDocument:
    body = {
        "arquivo_base64": base64.b64encode(content).decode("ascii"),
        "formato": format,
        "secao": declared,
        "politica": policy.model_dump(mode="json"),
    }
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.modules.knowledge.ingestion.worker"],
            input=json.dumps(body).encode(),
            capture_output=True,
            timeout=policy.timeout_seconds,
        )
        if result.returncode or len(result.stdout) > 67108864:
            return failed(Reason.ERRO_DO_PROCESSADOR)
        return ParsedDocument.model_validate_json(result.stdout)
    except subprocess.TimeoutExpired:
        return failed(Reason.TIMEOUT)
    except (OSError, ValidationError):
        return failed(Reason.ERRO_DO_PROCESSADOR)

import base64
import json
import sys

from app.modules.knowledge.ingestion.contracts import ExtractionPolicy, Reason
from app.modules.knowledge.ingestion.parser import failed, parse
from app.modules.knowledge.schemas import MAX_BASE64


def main() -> None:
    try:
        raw = sys.stdin.buffer.read(MAX_BASE64 + 65537)
        if len(raw) > MAX_BASE64 + 65536:
            result = failed(Reason.LIMITE_EXCEDIDO)
        else:
            request = json.loads(raw)
            result = parse(
                base64.b64decode(request["arquivo_base64"], validate=True),
                request["formato"],
                request["secao"],
                ExtractionPolicy.model_validate(request["politica"]),
            )
    except Exception:
        result = failed(Reason.ERRO_DO_PROCESSADOR)
    sys.stdout.buffer.write(result.model_dump_json().encode("utf-8"))


if __name__ == "__main__":
    main()

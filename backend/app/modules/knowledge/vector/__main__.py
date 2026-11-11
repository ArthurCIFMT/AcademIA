import json
from dataclasses import asdict

from app.modules.knowledge.vector.contracts import VectorError
from app.modules.knowledge.vector.runtime import close_vector_store, get_vector_store


def main() -> int:
    result: dict[str, object]
    code = 0
    try:
        try:
            report = get_vector_store().check()
            result = {"status": "OK", **asdict(report)}
        finally:
            close_vector_store()
    except VectorError as error:
        code = 1
        result = {"status": "ERRO", "code": error.code.value, "message": str(error)}
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

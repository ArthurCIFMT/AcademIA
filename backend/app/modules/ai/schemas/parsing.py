import json


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Chave JSON duplicada.")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("Número JSON não finito.")


def parse_object(text: str) -> dict[str, object]:
    result = json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    if not isinstance(result, dict):
        raise ValueError("Objeto JSON esperado.")
    return result

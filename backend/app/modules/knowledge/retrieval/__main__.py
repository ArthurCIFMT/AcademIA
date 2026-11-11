import argparse
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import create_database_engine, create_session_factory
from app.modules.knowledge.embeddings.runtime import close_encoder, get_encoder
from app.modules.knowledge.retrieval.contracts import Request
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.vector.runtime import close_vector_store, get_vector_store


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consulta técnica local ao corpus aprovado, sem LLM."
    )
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    engine = None
    try:
        with args.request.open("rb") as stream:
            body = stream.read(8193)
        if len(body) > 8192:
            raise ValueError("Entrada excessiva.")
        request = Request.model_validate_json(body)
        engine = create_database_engine("dev")
        result = Retriever(
            create_session_factory(engine), get_vector_store(), get_encoder()
        ).retrieve(request)
        print(result.model_dump_json())
        return 1 if result.estado == "SERVICO_INDISPONIVEL" else 0
    except (OSError, ValueError, ValidationError, SQLAlchemyError):
        print(
            '{"estado":"SERVICO_INDISPONIVEL","motivo":"CONSULTA_INVALIDA_OU_INDISPONIVEL"}'
        )
        return 1
    finally:
        try:
            close_encoder()
        finally:
            try:
                close_vector_store()
            finally:
                if engine is not None:
                    engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

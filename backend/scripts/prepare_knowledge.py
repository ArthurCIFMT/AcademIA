"""Prepara o corpus local; parar a API para liberar o diretório Qdrant."""

import argparse
import json
from pathlib import Path
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import create_database_engine, create_session_factory
from app.modules.knowledge.embeddings.encoder import EmbeddingError
from app.modules.knowledge.embeddings.runtime import close_encoder, get_encoder
from app.modules.knowledge.ingestion.indexing import IndexingError
from app.modules.knowledge.ingestion.service import ExtractionError
from app.modules.knowledge.preparation import prepare_corpus
from app.modules.knowledge.service import CorpusError
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.contracts import VectorError
from app.modules.knowledge.vector.runtime import close_vector_store, get_vector_store


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=UUID, required=True)
    args = parser.parse_args()
    engine = None
    try:
        engine = create_database_engine("dev")
        result = prepare_corpus(
            create_session_factory(engine),
            args.actor,
            CorpusStorage(),
            get_vector_store(),
            get_encoder(),
            root=Path(__file__).resolve().parents[2],
        )
        print(json.dumps(result.public(), default=str))
        return 0
    except (
        ValueError,
        OSError,
        SQLAlchemyError,
        CorpusError,
        VectorError,
        EmbeddingError,
        ExtractionError,
        IndexingError,
    ):
        print(
            json.dumps(
                {
                    "status": "ERRO",
                    "code": "PREPARACAO_NAO_CONCLUIDA",
                    "orientacao": (
                        "Confira curador, fontes, pesos locais e API parada."
                    ),
                }
            )
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

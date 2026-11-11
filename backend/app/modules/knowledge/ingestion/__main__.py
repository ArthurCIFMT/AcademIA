import argparse
import json
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import create_database_engine, create_session_factory
from app.modules.identity.roles import effective_roles
from app.modules.knowledge.embeddings.encoder import EmbeddingError
from app.modules.knowledge.embeddings.runtime import close_encoder, get_encoder
from app.modules.knowledge.ingestion.chunking import Selection
from app.modules.knowledge.ingestion.indexing import Indexer, IndexingError
from app.modules.knowledge.ingestion.service import ExtractionError, Extractor
from app.modules.knowledge.service import (
    CorpusError,
    approved_references,
    authorize,
    is_approved,
)
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.contracts import VectorError
from app.modules.knowledge.vector.runtime import close_vector_store, get_vector_store
from app.policies.access import Actor


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Indexação offline de literatura aprovada por curador ativo."
    )
    parser.add_argument("--actor", required=True, type=UUID)
    parser.add_argument("--version", required=True, type=UUID)
    parser.add_argument("--selection", required=True, type=Path)
    args = parser.parse_args()
    engine: Engine | None = None
    try:
        engine = create_database_engine("dev")
        sessions = create_session_factory(engine)
        with args.selection.open("rb") as file:
            body = file.read(2097153)
        if len(body) > 2097152:
            raise IndexingError("SELECAO_EXCEDE_LIMITE")
        selection = Selection.model_validate_json(body)
        with sessions.begin() as session:
            actor = Actor(args.actor, effective_roles(session, args.actor))
            authorize(actor)
            references = [
                ref
                for ref in approved_references(session)
                if ref.version_id == args.version
            ]
            if len(references) != 1:
                raise IndexingError("VERSAO_NAO_APROVADA")

        def approved(id: UUID, revision: int) -> bool:
            with sessions.begin() as session:
                return is_approved(session, id, revision)

        extraction = Extractor(CorpusStorage()).extract(
            references[0], approval_check=approved
        )
        encoder = get_encoder()
        result = Indexer(
            sessions,
            get_vector_store(),
            encoder,
            batch_size=encoder.settings.batch_size,
            timeout=encoder.settings.timeout_seconds,
        ).run(actor, extraction, selection)
        print(json.dumps({"status": "OK", **asdict(result)}, default=str))
        return 0 if result.estado == "CONCLUIDA" else 1
    except (
        IndexingError,
        ExtractionError,
        EmbeddingError,
        VectorError,
        CorpusError,
        ValidationError,
        OSError,
        SQLAlchemyError,
        ValueError,
    ):
        print('{"status":"ERRO","code":"INDEXACAO_NAO_CONCLUIDA"}')
        return 1
    finally:
        try:
            close_encoder()
        finally:
            close_vector_store()
            if engine is not None:
                engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

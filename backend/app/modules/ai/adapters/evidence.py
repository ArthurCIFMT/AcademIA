from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.ports.execution import Context
from app.modules.knowledge.ingestion.indexing import available_ingestions
from app.modules.knowledge.retrieval.contracts import Evidence, Request, Result, Scope
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Purpose
from app.modules.knowledge.service import is_approved
from app.modules.knowledge.vector.contracts import CollectionStatus, VectorError


class RagEvidence:
    def __init__(
        self,
        retriever: Retriever,
        sessions: sessionmaker[Session],
        status: Callable[[], CollectionStatus],
    ) -> None:
        self.retriever, self.sessions, self.status = retriever, sessions, status

    def retrieve(
        self, context: Context, purpose: Purpose, query: str, scope: Scope | None = None
    ) -> Result:
        return self.retriever.retrieve(
            Request(
                contexto_id=context.client_id,
                finalidade=purpose,
                consulta=query,
                escopo_saude=scope,
            )
        )

    def current(self, evidences: tuple[Evidence, ...]) -> bool:
        try:
            status = self.status()
            with self.sessions.begin() as session:
                allowed = set(
                    available_ingestions(
                        session, status.collection, status.space_sha256
                    )
                )
                return all(
                    e.ingestao_id in allowed
                    and is_approved(session, e.documento_versao_id, e.aprovacao_revisao)
                    for e in evidences
                )
        except (SQLAlchemyError, VectorError):
            return False

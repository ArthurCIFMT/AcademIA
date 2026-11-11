"""Porta SQL de proveniência para a transação final de publicação."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge.ingestion.index_models import Fragment, Ingestion
from app.modules.knowledge.models import DocumentVersion
from app.modules.knowledge.retrieval.contracts import Evidence


def lock_publication_evidence(
    session: Session, evidences: tuple[Evidence, ...]
) -> bool:
    if not evidences:
        return False
    for e in sorted(
        evidences, key=lambda item: (item.documento_versao_id, item.fragmento_id)
    ):
        document = session.scalar(
            select(DocumentVersion)
            .where(DocumentVersion.id == e.documento_versao_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        ingestion = session.scalar(
            select(Ingestion)
            .where(Ingestion.id == e.ingestao_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        fragment = session.scalar(
            select(Fragment)
            .where(Fragment.id == e.fragmento_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if (
            not document
            or not ingestion
            or not fragment
            or document.estado != "APROVADO"
            or document.ambiente != "LITERATURA"
            or document.revision != e.aprovacao_revisao
            or ingestion.estado != "CONCLUIDA"
            or ingestion.documento_versao_id != document.id
            or ingestion.aprovacao_revisao != document.revision
            or fragment.ingestao_id != ingestion.id
            or fragment.indexado_em is None
            or fragment.texto_hash != e.texto_hash
        ):
            return False
    return True

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.structured import StrictModel
from app.contracts.time import UtcTimestamp
from app.modules.ai.chat.models import Message
from app.modules.ai.followup import Source
from app.modules.ai.persistence.models import EvidenceRecord
from app.modules.ai.ports.execution import ExecutionConflict
from app.modules.ai.schemas.execution import ChatAnswer, RunResult
from app.modules.identity.service import utc_now
from app.modules.knowledge.service import is_approved


class ChatView(StrictModel):
    solicitacao_id: UUID
    pergunta: str
    criada_em: UtcTimestamp
    finalidade: str
    estado: str
    motivo: str
    resposta: ChatAnswer | None
    fontes: list[Source]
    versao_publicada_id: UUID | None


def present(
    session: Session, message: Message, receipt: RunResult | None, current: UUID | None
) -> ChatView:
    if message.criada_em < utc_now() - timedelta(days=90):
        raise ExecutionConflict()
    answer = receipt.resposta if receipt else None
    stale = (
        message.pedido["finalidade"] == "DUVIDA"
        and message.versao_contexto_id != current
    )
    sources = []
    if answer:
        for record in session.scalars(
            select(EvidenceRecord).where(
                EvidenceRecord.execucao_id == message.id,
                EvidenceRecord.fragmento_id.in_(answer.evidencias_ids),
            )
        ):
            data = record.metadados
            source = Source.model_validate(data)
            if not is_approved(
                session, source.documento_versao_id, int(str(data["aprovacao_revisao"]))
            ):
                stale = True
            sources.append(source)
    if stale:
        answer = None
        sources = []
    return ChatView(
        solicitacao_id=message.solicitacao_id,
        pergunta=message.pergunta,
        criada_em=message.criada_em,
        finalidade=str(message.pedido["finalidade"]),
        estado="ABSTENCAO"
        if stale
        else receipt.estado
        if receipt
        else (
            "INTERROMPIDA"
            if message.criada_em < utc_now() - timedelta(seconds=100)
            and message.estado == "RESERVADA"
            else "AGUARDANDO"
            if message.estado == "RESERVADA"
            else message.estado
        ),
        motivo="CONTEXTO_OU_FONTES_SUPERADOS"
        if stale
        else receipt.motivo
        if receipt
        else message.erro_codigo or "EXECUCAO_NAO_INICIADA",
        resposta=answer,
        fontes=sources,
        versao_publicada_id=receipt.versao_publicada_id if receipt else None,
    )

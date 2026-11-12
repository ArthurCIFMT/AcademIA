"""Expurgo de conteúdo privado; recibos, orçamento e proveniência são preservados."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.persistence.models import Execution, TriageRecord
from app.modules.ai.schemas.execution import RunResult
from app.modules.identity.service import utc_now


def strip_private(result: RunResult) -> RunResult:
    return result.model_copy(
        update={"triagem": None, "resposta": None, "proposta": None, "evidencias": []}
    )


def purge_expired(sessions: sessionmaker[Session]) -> int:
    from app.modules.ai.chat.service import purge_messages

    purge_messages(sessions)
    cutoff = utc_now() - timedelta(days=90)
    with sessions.begin() as session:
        rows = list(
            session.scalars(
                select(Execution)
                .where(Execution.terminada_em < cutoff)
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            row.resultado = strip_private(
                RunResult.model_validate(row.resultado)
            ).model_dump(mode="json", exclude={"proposta", "evidencias"})
            triage = session.scalar(
                select(TriageRecord).where(TriageRecord.execucao_id == row.id)
            )
            if triage:
                triage.resumo = {}
        return len(rows)


if __name__ == "__main__":
    from app.database.connection import create_database_engine, create_session_factory

    engine = create_database_engine("dev")
    try:
        print(f"Execuções processadas: {purge_expired(create_session_factory(engine))}")
    finally:
        engine.dispose()

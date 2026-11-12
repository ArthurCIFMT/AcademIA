from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, or_, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.adapters.health_config import ConfiguredContext
from app.modules.ai.chat.models import Conversation, Message
from app.modules.ai.chat.quota import occupied_slots
from app.modules.ai.chat.views import ChatView, present
from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.models import Execution
from app.modules.ai.persistence.state import PostgresState, RateLimited
from app.modules.ai.ports.execution import (
    ContextDenied,
    ExecutionConflict,
    ProviderError,
)
from app.modules.ai.schemas.execution import (
    PlanDay,
    PlanItem,
    PlanOutline,
    RunRequest,
    RunResult,
)
from app.modules.identity.service import utc_now
from app.modules.onboarding.service import get_current_snapshot
from app.modules.training.generated import current_generation_base
from app.modules.training.publication import published_workout
from app.modules.training.workouts import WorkoutError
from app.policies.access import Actor


class ChatService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        generator: GenerationService | None = None,
    ) -> None:
        self.sessions = sessions
        self.generator = generator or GenerationService(
            sessions, contexts=ConfiguredContext(sessions, base_reader=self.base)
        )

    def base(self, actor: Actor, client: UUID, version: UUID) -> PlanOutline | None:
        with self.sessions.begin() as session:
            detail = published_workout(session, actor, client, version)
            if not detail or not detail.ficha.dias or not detail.ficha.vigente:
                return None
            days = [
                PlanDay(
                    titulo=d.titulo,
                    itens=[
                        PlanItem.model_validate(
                            {
                                **i.model_dump(exclude={"exercicio_snapshot"}),
                                "ordem": n,
                                "observacoes": i.observacoes or "",
                            }
                        )
                        for n, i in enumerate(d.itens, 1)
                    ],
                )
                for d in detail.ficha.dias
            ]
            # Base de domínio, sem inventar evidências para a saída do modelo.
            return PlanOutline(dias=days)

    def ask(
        self, actor: Actor, request: RunRequest, onboarding_id: UUID | None = None
    ) -> RunResult:
        if request.finalidade not in {"DUVIDA", "ADAPTACAO"}:
            raise ValueError("Use o fluxo de geração para uma ficha inicial.")
        self.generator.authorize(actor, actor.user_id)
        with self.sessions.begin() as session:
            session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:client, 0))"),
                {"client": str(actor.user_id)},
            )
            id = PostgresState.id(actor, request.solicitacao_id)
            old = session.get(Message, id)
            current = current_generation_base(session, actor, actor.user_id)
            if old:
                saved = RunRequest.model_validate(old.pedido)
                if (
                    saved.mensagem != request.mensagem
                    or saved.finalidade != request.finalidade
                    or saved.versao_base_id != request.versao_base_id
                    or saved.dia_alvo != request.dia_alvo
                    or saved.onboarding_confirmado_id
                    != request.onboarding_confirmado_id
                ):
                    raise ExecutionConflict()
                if saved.finalidade == "DUVIDA" and (
                    old.versao_contexto_id != current
                    or old.criada_em < utc_now() - timedelta(days=90)
                ):
                    raise ExecutionConflict()
                if (
                    saved.finalidade == "ADAPTACAO"
                    and current != saved.versao_base_id
                    and session.get(Execution, id) is None
                ):
                    raise ExecutionConflict()
                if session.get(
                    Execution, id
                ) is None and old.criada_em < utc_now() - timedelta(seconds=100):
                    raise ExecutionConflict()
                request = saved
            else:
                if session.get(Execution, id) is not None:
                    raise ExecutionConflict()
                if occupied_slots(session, actor.user_id) >= 6:
                    raise RateLimited()
                current = current_generation_base(session, actor, actor.user_id)
                if request.finalidade == "ADAPTACAO":
                    snapshot = get_current_snapshot(session, actor.user_id)
                    if (
                        not snapshot
                        or snapshot.id != onboarding_id
                        or snapshot.id != request.onboarding_confirmado_id
                        or current != request.versao_base_id
                        or not request.dia_alvo
                    ):
                        raise WorkoutError(409)
                if not session.get(Conversation, actor.user_id):
                    session.add(Conversation(id=actor.user_id))
                    session.flush()
                # Usar perguntas recentes somente do mesmo contexto.
                previous = list(
                    session.scalars(
                        select(Message)
                        .where(
                            Message.conversa_id == actor.user_id,
                            Message.versao_contexto_id == current,
                            Message.criada_em >= utc_now() - timedelta(days=90),
                        )
                        .order_by(Message.criada_em.desc())
                        .limit(3)
                    )
                )
                history = [
                    {"papel": "user", "texto": m.pergunta}
                    for m in reversed(previous)
                    if m.pedido.get("finalidade") == "DUVIDA"
                ]
                request = RunRequest.model_validate(
                    {
                        **request.model_dump(mode="json"),
                        "historico": history if request.finalidade == "DUVIDA" else [],
                    }
                )
                session.add(
                    Message(
                        id=id,
                        conversa_id=actor.user_id,
                        solicitacao_id=request.solicitacao_id,
                        pergunta=request.mensagem,
                        estado="RESERVADA",
                        erro_codigo=None,
                        pedido=request.model_dump(mode="json"),
                        versao_contexto_id=current,
                        criada_em=utc_now(),
                    )
                )
        try:
            result = self.generator.generate(actor, actor.user_id, request)
        except (ProviderError, ValueError, ContextDenied, WorkoutError, RateLimited):
            with self.sessions.begin() as session:
                message = session.get(Message, id)
                if message:
                    message.estado = "FALHA"
                    message.erro_codigo = "PREPARACAO_RECUSADA"
            raise
        with self.sessions.begin() as session:
            message = session.get(Message, id)
            if message:
                message.estado = result.estado
                message.erro_codigo = None
        return result

    def adaptation_context(self, actor: Actor) -> dict[str, object]:
        self.generator.authorize(actor, actor.user_id)
        with self.sessions.begin() as session:
            version = current_generation_base(session, actor, actor.user_id)
            snapshot = get_current_snapshot(session, actor.user_id)
            if not version or not snapshot:
                raise WorkoutError(409)
            detail = published_workout(session, actor, actor.user_id, version)
            if not detail or not detail.ficha.dias:
                raise WorkoutError(409)
            return {
                "versao_base_id": str(version),
                "onboarding_id": str(snapshot.id),
                "snapshot_numero": snapshot.numero,
                "dias": [day.titulo for day in detail.ficha.dias],
            }

    def turn(self, actor: Actor, id: UUID) -> ChatView:
        self.generator.authorize(actor, actor.user_id)
        with self.sessions.begin() as session:
            message = session.get(Message, PostgresState.id(actor, id))
            if message is None or message.conversa_id != actor.user_id:
                raise KeyError(id)
            request = RunRequest.model_validate(message.pedido)
        receipt = PostgresState(self.sessions).lookup(actor, actor.user_id, request)
        with self.sessions.begin() as session:
            current = current_generation_base(session, actor, actor.user_id)
            return present(session, message, receipt, current)

    def history(self, actor: Actor, page: int) -> list[ChatView]:
        self.generator.authorize(actor, actor.user_id)
        with self.sessions.begin() as session:
            current = current_generation_base(session, actor, actor.user_id)
            rows = list(
                session.scalars(
                    select(Message.solicitacao_id)
                    .where(
                        Message.conversa_id == actor.user_id,
                        or_(
                            Message.versao_contexto_id == current,
                            Message.id.in_(
                                select(Execution.id).where(
                                    Execution.versao_publicada_id == current
                                )
                            )
                            if current
                            else Message.versao_contexto_id.is_(None),
                        ),
                        Message.criada_em >= utc_now() - timedelta(days=90),
                    )
                    .order_by(Message.criada_em.desc(), Message.id)
                    .offset((page - 1) * 20)
                    .limit(20)
                )
            )
        views = []
        for id in reversed(rows):
            try:
                views.append(self.turn(actor, id))
            except (KeyError, ExecutionConflict):
                continue
        return views

    def differences(self, actor: Actor, id: UUID) -> dict[str, object]:
        view = self.turn(actor, id)
        if not view.versao_publicada_id or view.finalidade != "ADAPTACAO":
            raise WorkoutError(409)
        with self.sessions.begin() as session:
            message = session.get(Message, PostgresState.id(actor, id))
            assert message is not None
            base = RunRequest.model_validate(message.pedido).versao_base_id
            old = (
                published_workout(session, actor, actor.user_id, base) if base else None
            )
            new = published_workout(
                session, actor, actor.user_id, view.versao_publicada_id
            )
            if not old or not new:
                raise WorkoutError(404)
            return {
                "anterior": old.model_dump(mode="json"),
                "atual": new.model_dump(mode="json"),
                "conteudo_expirado": bool(
                    old.ficha.conteudo_excluido_em or new.ficha.conteudo_excluido_em
                ),
            }


def purge_messages(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.execute(
            delete(Message).where(Message.criada_em < utc_now() - timedelta(days=90))
        )

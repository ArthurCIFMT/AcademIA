from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.errors import HeaderParseError
from email.headerregistry import Address
from email.message import EmailMessage
from smtplib import SMTP, SMTPRecipientsRefused, SMTPResponseException
from typing import Annotated, Literal, Protocol, cast
from uuid import UUID, uuid4

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from app.modules.notifications.models import DeliveryState, EmailKind, Notification

_MAX_ATTEMPTS = 3
_SUBJECTS = {
    EmailKind.PRIMEIRO_ACESSO: "AcademIA — Primeiro acesso",
    EmailKind.RECUPERACAO: "AcademIA — Recuperação de acesso",
    EmailKind.CONVITE_ONBOARDING: "AcademIA — Convite para onboarding",
    EmailKind.TREINO_PARA_AVALIAR: "AcademIA — Treino para avaliar",
    EmailKind.ALTERACAO_CRITICA: "AcademIA — Alteração crítica",
}


class SmtpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_SMTP_", hide_input_in_errors=True
    )

    host: Literal["127.0.0.1", "::1"] = "127.0.0.1"
    port: Annotated[int, Field(ge=1, le=65535)] = 1025
    sender: str = "academia@example.test"
    timeout: Annotated[float, Field(gt=0, le=30)] = 5


@dataclass(frozen=True)
class EmailRequest:
    event_id: UUID
    recipient_id: UUID
    kind: EmailKind
    address: str = field(repr=False)
    body: str = field(repr=False)


@dataclass(frozen=True)
class DeliveryResult:
    state: DeliveryState
    attempts: int


class MailTransport(Protocol):
    def deliver(self, message: EmailMessage) -> DeliveryState: ...


class LocalSmtp:
    def __init__(self, settings: SmtpSettings) -> None:
        self.settings = settings

    def deliver(self, message: EmailMessage) -> DeliveryState:
        client = SMTP(timeout=self.settings.timeout, local_hostname="localhost")
        try:
            try:
                code, _ = client.connect(self.settings.host, self.settings.port)
                if code != 220:
                    return DeliveryState.FALHOU
            except OSError:
                return DeliveryState.FALHOU
            try:
                client.send_message(message)
            except (SMTPRecipientsRefused, SMTPResponseException):
                return DeliveryState.FALHOU
            except OSError:
                # A conexão pode cair depois que o servidor aceitou a mensagem.
                return DeliveryState.INCERTO
            return DeliveryState.ENVIADO
        finally:
            client.close()


def _message(request: EmailRequest, sender: str) -> EmailMessage:
    message = EmailMessage()
    try:
        message["From"] = Address(addr_spec=sender)
        message["To"] = Address(addr_spec=request.address)
    except (HeaderParseError, ValueError, IndexError):
        raise ValueError("Endereço de e-mail inválido.") from None
    message["Subject"] = _SUBJECTS[request.kind]
    message["Message-ID"] = (
        f"<{request.event_id}.{request.recipient_id}@academia.example.test>"
    )
    message.set_content(request.body)
    return message


class EmailDelivery:
    def __init__(
        self, sessions: sessionmaker[Session], transport: MailTransport, sender: str
    ) -> None:
        self.sessions = sessions
        self.transport = transport
        self.sender = sender

    def send(
        self, request: EmailRequest, *, retry_after: int | None = None
    ) -> DeliveryResult:
        """Reserva uma tentativa durável antes do I/O e guarda só o resultado."""
        message = _message(request, self.sender)
        with self.sessions.begin() as session:
            reservation = self._reserve(session, request, retry_after=retry_after)
        if isinstance(reservation, DeliveryResult):
            return reservation

        state = self.transport.deliver(message)
        with self.sessions.begin() as session:
            record = session.get(Notification, reservation)
            if record is None:
                raise RuntimeError("Reserva de envio ausente.")
            record.estado = state
            record.atualizada_em = datetime.now(UTC)
            return DeliveryResult(state, record.tentativas)

    def _reserve(
        self, session: Session, request: EmailRequest, *, retry_after: int | None
    ) -> UUID | DeliveryResult:
        now = datetime.now(UTC)
        if retry_after is None:
            created = session.scalar(
                insert(Notification)
                .values(
                    id=uuid4(),
                    destinatario_id=request.recipient_id,
                    evento_id=request.event_id,
                    canal="EMAIL",
                    tipo=request.kind,
                    estado=DeliveryState.ENVIANDO,
                    tentativas=1,
                    criada_em=now,
                    atualizada_em=now,
                )
                .on_conflict_do_nothing(constraint="uq_notificacao_dest_evento_canal")
                .returning(Notification.id)
            )
            if created is not None:
                return cast(UUID, created)

        previous = session.scalar(
            select(Notification)
            .where(
                Notification.destinatario_id == request.recipient_id,
                Notification.evento_id == request.event_id,
                Notification.canal == "EMAIL",
            )
            .with_for_update()
        )
        if previous is None or previous.tipo != request.kind:
            raise ValueError("Envio anterior inexistente ou de outra finalidade.")
        if (
            previous.estado == DeliveryState.FALHOU
            and previous.tentativas == retry_after
            and previous.tentativas < _MAX_ATTEMPTS
        ):
            previous.estado = DeliveryState.ENVIANDO
            previous.tentativas += 1
            previous.atualizada_em = now
            return previous.id
        return DeliveryResult(DeliveryState(previous.estado), previous.tentativas)


def local_email_delivery(sessions: sessionmaker[Session]) -> EmailDelivery:
    settings = SmtpSettings()
    return EmailDelivery(sessions, LocalSmtp(settings), settings.sender)

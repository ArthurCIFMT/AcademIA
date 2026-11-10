from email.message import EmailMessage
from os import environ
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.modules.notifications.email import LocalSmtp, SmtpSettings
from app.modules.notifications.models import DeliveryState


def test_smtp_host_rejects_external_targets() -> None:
    with pytest.raises(ValidationError):
        SmtpSettings.model_validate({"host": "smtp.example.test"})


@pytest.mark.integration
def test_delivers_once_to_mailpit() -> None:
    if environ.get("ACADEMIA_TEST_MAILPIT") != "1":
        pytest.skip("Inicie o Mailpit local e configure ACADEMIA_TEST_MAILPIT=1.")

    message = EmailMessage()
    message_id = f"{uuid4()}@academia.example.test"
    message["Message-ID"] = f"<{message_id}>"
    message["From"] = "academia@example.test"
    message["To"] = "instrutor@example.test"
    message["Subject"] = "Teste sintético NTF-01"
    message.set_content("Treino disponível para avaliação.")
    transport = LocalSmtp(SmtpSettings())

    assert transport.deliver(message) == DeliveryState.ENVIADO
    assert transport.deliver(message) == DeliveryState.ENVIADO
    reply = httpx.get(
        "http://127.0.0.1:8025/api/v1/messages", timeout=5, trust_env=False
    )
    reply.raise_for_status()
    matched = [
        item for item in reply.json()["messages"] if item["MessageID"] == message_id
    ]
    assert len(matched) == 1
    assert matched[0]["Subject"] == "Teste sintético NTF-01"

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AccessDecision(Base):
    __tablename__ = "decisao_acesso"
    __table_args__ = (
        CheckConstraint(
            "resultado IN ('ALLOW', 'DENY')", name="ck_decisao_acesso_resultado"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), unique=True
    )
    matricula_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.matricula.id")
    )
    resultado: Mapped[str] = mapped_column(String(15))
    motivo: Mapped[str] = mapped_column(String(80))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    regra_json: Mapped[dict[str, str | int | None]] = mapped_column(JSONB)


class TurnstileCommand(Base):
    __tablename__ = "catraca_comando"
    __table_args__ = (
        CheckConstraint("direcao IN ('ENTRY', 'EXIT')", name="ck_catraca_direcao"),
        CheckConstraint(
            "estado IN ('CRIADO', 'ACEITO', 'FALHOU', 'CONFIRMADO')",
            name="ck_catraca_estado",
        ),
        CheckConstraint(
            "(estado = 'CONFIRMADO') = (passagem_evento_id IS NOT NULL)",
            name="ck_catraca_passagem",
        ),
        CheckConstraint(
            "(estado = 'FALHOU') = (falha_envio IS NOT NULL)", name="ck_catraca_falha"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    decisao_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.decisao_acesso.id"), unique=True
    )
    request_id: Mapped[UUID] = mapped_column(unique=True)
    direcao: Mapped[str] = mapped_column(String(15))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(25))
    passagem_evento_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.evento_acesso.id"), unique=True
    )
    falha_envio: Mapped[str | None] = mapped_column(String(25))

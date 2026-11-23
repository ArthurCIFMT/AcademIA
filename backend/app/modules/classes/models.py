from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ClassState(StrEnum):
    AGENDADA = "AGENDADA"
    CANCELADA = "CANCELADA"


class ClassOccurrence(Base):
    __tablename__ = "aula_ocorrencia"
    __table_args__ = (
        CheckConstraint("length(btrim(nome)) > 0", name="ck_aula_nome"),
        CheckConstraint("fim > inicio", name="ck_aula_intervalo"),
        CheckConstraint("estado IN ('AGENDADA', 'CANCELADA')", name="ck_aula_estado"),
        CheckConstraint("revision >= 1", name="ck_aula_revision"),
        Index("ix_aula_inicio_id", "inicio", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    descricao: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(25))
    revision: Mapped[int]

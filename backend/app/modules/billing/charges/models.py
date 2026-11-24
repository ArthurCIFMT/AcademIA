from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Charge(Base):
    __tablename__ = "cobranca"
    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_cobranca_valor"),
        CheckConstraint(
            "extract(day from competencia) = 1", name="ck_cobranca_competencia"
        ),
        CheckConstraint("estado IN ('ABERTA', 'CANCELADA')", name="ck_cobranca_estado"),
        CheckConstraint("revisao >= 1", name="ck_cobranca_revisao"),
        UniqueConstraint("id", "cliente_id", name="uq_cobranca_cliente_id"),
        ForeignKeyConstraint(
            ["matricula_id", "cliente_id"],
            ["academia.matricula.id", "academia.matricula.cliente_id"],
            name="fk_cobranca_matricula_cliente",
        ),
        Index("ix_cobranca_cliente_competencia", "cliente_id", "competencia"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    matricula_id: Mapped[UUID | None]
    competencia: Mapped[date]
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vencimento: Mapped[date]
    estado: Mapped[str] = mapped_column(String(25))
    revisao: Mapped[int]


class ChargeRevision(Base):
    __tablename__ = "cobranca_revisao"
    __table_args__ = (
        CheckConstraint("revisao >= 1", name="ck_cobranca_revisao_numero"),
        UniqueConstraint("cobranca_id", "revisao", name="uq_cobranca_revisao_numero"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cobranca_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cobranca.id"))
    revisao: Mapped[int]
    autor_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dados: Mapped[dict[str, str | None]] = mapped_column(JSONB)

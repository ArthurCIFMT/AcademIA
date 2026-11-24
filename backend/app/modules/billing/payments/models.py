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
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

_MANUAL_PAYMENT = """origem <> 'MANUAL' OR (
    referencia_externa IS NOT NULL
    AND referencia_externa = btrim(referencia_externa)
    AND referencia_externa <> ''
    AND valor > 0 AND estado IN ('CONFIRMADO', 'ANULADO')
    AND metodo IS NOT NULL
    AND metodo IN ('PIX', 'DINHEIRO', 'CARTAO', 'TRANSFERENCIA', 'OUTRO')
    AND pago_em IS NOT NULL AND confirmado_em IS NOT NULL
    AND registrado_por_id IS NOT NULL
    AND (
        (estado = 'CONFIRMADO' AND anulado_em IS NULL AND anulado_por_id IS NULL
         AND motivo_anulacao IS NULL)
        OR
        (estado = 'ANULADO' AND anulado_em IS NOT NULL AND anulado_por_id IS NOT NULL
         AND motivo_anulacao IS NOT NULL AND btrim(motivo_anulacao) <> ''
         AND anulado_em >= confirmado_em)
    )
)"""
_MANUAL_CONFIRMED = "origem = 'MANUAL' AND estado = 'CONFIRMADO'"
_REPLACEMENT = "substitui_id IS NULL OR (origem = 'MANUAL' AND substitui_id <> id)"


class Payment(Base):
    __tablename__ = "pagamento"
    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_pagamento_valor"),
        CheckConstraint(_MANUAL_PAYMENT, name="ck_pagamento_manual"),
        CheckConstraint(_REPLACEMENT, name="ck_pagamento_substituicao"),
        UniqueConstraint("id", "cliente_id", name="uq_pagamento_cliente_id"),
        ForeignKeyConstraint(
            ["substitui_id", "cliente_id"],
            ["academia.pagamento.id", "academia.pagamento.cliente_id"],
            name="fk_pagamento_substituido_cliente",
        ),
        ForeignKeyConstraint(
            ["cobranca_id", "cliente_id"],
            ["academia.cobranca.id", "academia.cobranca.cliente_id"],
            name="fk_pagamento_cobranca_cliente",
        ),
        Index("ix_pagamento_cliente", "cliente_id"),
        Index("ix_pagamento_cobranca", "cobranca_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    cobranca_id: Mapped[UUID | None]
    plano_id: Mapped[UUID | None] = mapped_column(ForeignKey("academia.plano.id"))
    origem: Mapped[str] = mapped_column(String(25))
    referencia_externa: Mapped[str | None] = mapped_column(String(150))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[str] = mapped_column(String(25))
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metodo: Mapped[str | None] = mapped_column(String(25))
    pago_em: Mapped[date | None]
    registrado_por_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    substitui_id: Mapped[UUID | None] = mapped_column(unique=True)
    anulado_por_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    anulado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_anulacao: Mapped[str | None] = mapped_column(String(240))


Index(
    "uq_pagamento_manual_referencia",
    func.lower(Payment.referencia_externa),
    unique=True,
    postgresql_where=text(_MANUAL_CONFIRMED),
)

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AccessEvent(Base):
    __tablename__ = "evento_acesso"
    __table_args__ = (
        UniqueConstraint(
            "origem", "event_id_externo", name="uq_evento_acesso_origem_id"
        ),
        CheckConstraint(
            "direcao IN ('ENTRADA', 'SAIDA')", name="ck_evento_acesso_direcao"
        ),
        CheckConstraint(
            "similaridade BETWEEN 0 AND 1", name="ck_evento_acesso_similaridade"
        ),
        CheckConstraint(
            """tipo <> 'IDENTIFICACAO' OR (
                resultado_identificacao IS NOT NULL
                AND resultado_identificacao IN (
                    'IDENTIFICADO', 'DESCONHECIDO', 'PONTUACAO_BAIXA', 'AMBIGUO',
                    'CAPTURA_INVALIDA', 'FALHA_PROVEDOR'
                )
                AND ((resultado_identificacao = 'IDENTIFICADO')
                     = (cliente_id IS NOT NULL))
                AND (resultado_identificacao <> 'IDENTIFICADO'
                     OR similaridade IS NOT NULL)
            )""",
            name="ck_evento_acesso_identificacao",
        ),
        CheckConstraint(
            """tipo <> 'IDENTIFICACAO_MANUAL' OR (
                origem = 'ATENDIMENTO_MANUAL' AND cliente_id IS NOT NULL
                AND similaridade IS NULL AND resultado_identificacao IS NOT NULL
                AND resultado_identificacao = 'IDENTIFICADO'
            )""",
            name="ck_evento_acesso_manual",
        ),
        CheckConstraint(
            """resultado_presenca IS NULL OR (
                tipo = 'PASSAGEM_SIMULADA' AND origem = 'CATRACA_SIMULADA'
                AND cliente_id IS NOT NULL
                AND resultado_presenca IN (
                    'ENTRADA_REGISTRADA', 'SAIDA_REGISTRADA',
                    'ENTRADA_REPETIDA', 'SAIDA_SEM_ENTRADA'
                )
            )""",
            name="ck_evento_acesso_resultado_presenca",
        ),
        Index(
            "ix_evento_acesso_passagem_cliente",
            "cliente_id",
            "ocorrido_em",
            "id",
            postgresql_where=text(
                "tipo = 'PASSAGEM_SIMULADA' AND origem = 'CATRACA_SIMULADA'"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    origem: Mapped[str] = mapped_column(String(80))
    event_id_externo: Mapped[str] = mapped_column(String(120))
    cliente_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("academia.cliente.usuario_id")
    )
    tipo: Mapped[str] = mapped_column(String(25))
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload_hash: Mapped[str] = mapped_column(CHAR(64))
    direcao: Mapped[str] = mapped_column(String(10))
    resultado_identificacao: Mapped[str | None] = mapped_column(String(24))
    resultado_presenca: Mapped[str | None] = mapped_column(String(24))
    similaridade: Mapped[float | None] = mapped_column(Float)

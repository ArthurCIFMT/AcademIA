from __future__ import annotations

from datetime import datetime
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
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WorkoutVersion(Base):
    __tablename__ = "versao_ficha"
    __table_args__ = (
        UniqueConstraint("cliente_id", "numero", name="uq_ficha_cliente_numero"),
        UniqueConstraint("cliente_id", "id", name="uq_ficha_cliente_id"),
        ForeignKeyConstraint(
            ["cliente_id", "onboarding_id"],
            ["academia.onboarding_versao.cliente_id", "academia.onboarding_versao.id"],
            name="fk_ficha_onboarding_cliente",
        ),
        ForeignKeyConstraint(
            ["cliente_id", "onboarding_id", "avaliacao_id"],
            [
                "academia.avaliacao.cliente_id",
                "academia.avaliacao.onboarding_id",
                "academia.avaliacao.id",
            ],
            name="fk_ficha_avaliacao_contexto",
        ),
        ForeignKeyConstraint(
            ["cliente_id", "versao_base_id"],
            ["academia.versao_ficha.cliente_id", "academia.versao_ficha.id"],
            name="fk_ficha_base_cliente",
        ),
        CheckConstraint(
            "numero >= 1 AND revision >= 1 AND "
            "((origem = 'MANUAL' AND autor_id IS NOT NULL) OR origem = 'IA')",
            name="ck_ficha_identificacao",
        ),
        CheckConstraint(
            "(estado_publicacao = 'RASCUNHO' AND NOT vigente AND publicada_em IS NULL "
            "AND conteudo_excluido_em IS NULL AND motivo_exclusao IS NULL) OR "
            "(estado_publicacao IN ('PUBLICADO', 'SUBSTITUIDO') "
            "AND vigente = (estado_publicacao = 'PUBLICADO') "
            "AND publicada_em IS NOT NULL AND conteudo_excluido_em IS NULL "
            "AND motivo_exclusao IS NULL) OR "
            "(estado_publicacao = 'CONTEUDO_EXPIRADO' AND NOT vigente "
            "AND publicada_em IS NOT NULL AND conteudo_excluido_em IS NOT NULL "
            "AND motivo_exclusao IN ('LIMITE_15', 'REJEITADA_ANTERIOR'))",
            name="ck_ficha_publicacao",
        ),
        Index(
            "uq_ficha_vigente",
            "cliente_id",
            unique=True,
            postgresql_where=text("vigente"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    numero: Mapped[int]
    origem: Mapped[str] = mapped_column(String(20))
    autor_id: Mapped[UUID | None] = mapped_column(ForeignKey("academia.usuario.id"))
    onboarding_id: Mapped[UUID]
    avaliacao_id: Mapped[UUID | None]
    versao_base_id: Mapped[UUID | None]
    estado_publicacao: Mapped[str] = mapped_column(String(25))
    vigente: Mapped[bool]
    publicada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conteudo_excluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    motivo_exclusao: Mapped[str | None] = mapped_column(String(40))
    revision: Mapped[int]
    dias: Mapped[list[WorkoutDay]] = relationship(
        cascade="all, delete-orphan",
        order_by="WorkoutDay.ordem",
    )


class WorkoutDay(Base):
    __tablename__ = "dia_ficha"
    __table_args__ = (
        UniqueConstraint("versao_id", "ordem", name="uq_ficha_dia_ordem"),
        CheckConstraint(
            "ordem >= 1 AND length(btrim(titulo)) > 0", name="ck_ficha_dia"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    versao_id: Mapped[UUID] = mapped_column(ForeignKey("academia.versao_ficha.id"))
    ordem: Mapped[int]
    titulo: Mapped[str] = mapped_column(String(60))
    itens: Mapped[list[WorkoutItem]] = relationship(
        cascade="all, delete-orphan",
        order_by="WorkoutItem.ordem",
    )


class WorkoutItem(Base):
    __tablename__ = "item_ficha"
    __table_args__ = (
        UniqueConstraint("dia_id", "ordem", name="uq_ficha_item_ordem"),
        CheckConstraint(
            "ordem >= 1 AND series BETWEEN 1 AND 100 "
            "AND length(btrim(repeticoes)) > 0 "
            "AND intervalo_segundos BETWEEN 0 AND 3600 "
            "AND (carga_kg IS NULL OR carga_kg >= 0) "
            "AND jsonb_typeof(exercicio_snapshot) = 'object'",
            name="ck_ficha_item",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    dia_id: Mapped[UUID] = mapped_column(ForeignKey("academia.dia_ficha.id"))
    exercicio_id: Mapped[UUID] = mapped_column(ForeignKey("academia.exercicio.id"))
    ordem: Mapped[int]
    series: Mapped[int]
    repeticoes: Mapped[str] = mapped_column(String(40))
    carga_kg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    intervalo_segundos: Mapped[int]
    cadencia: Mapped[str | None] = mapped_column(String(40))
    observacoes: Mapped[str | None] = mapped_column(Text)
    exercicio_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB)


class WorkoutOpinion(Base):
    __tablename__ = "parecer"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('PENDENTE', 'ACEITO', 'REJEITADO')", name="ck_parecer_estado"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    versao_id: Mapped[UUID] = mapped_column(ForeignKey("academia.versao_ficha.id"))
    instrutor_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    estado: Mapped[str] = mapped_column(String(20))
    motivo: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

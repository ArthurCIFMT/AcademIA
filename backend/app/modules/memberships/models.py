from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.modules.memberships.schemas import MembershipState


class Plan(Base):
    __tablename__ = "plano"
    __table_args__ = (
        CheckConstraint("btrim(nome) <> ''", name="ck_plano_nome"),
        CheckConstraint("btrim(modalidade) <> ''", name="ck_plano_modalidade"),
        CheckConstraint("duracao_dias > 0", name="ck_plano_duracao"),
        CheckConstraint("limite_acessos > 0", name="ck_plano_limite"),
        CheckConstraint(
            "(limite_acessos IS NULL AND janela_limite IS NULL) OR "
            "(limite_acessos IS NOT NULL AND janela_limite IS NOT NULL "
            "AND janela_limite = 'DIA_CIVIL')",
            name="ck_plano_janela",
        ),
        CheckConstraint("preco_base >= 0", name="ck_plano_preco"),
        CheckConstraint("revision >= 1", name="ck_plano_revision"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    duracao_dias: Mapped[int]
    modalidade: Mapped[str] = mapped_column(String(80))
    limite_acessos: Mapped[int | None]
    janela_limite: Mapped[str | None] = mapped_column(String(25))
    preco_base: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    ativo: Mapped[bool]
    revision: Mapped[int]


class Membership(Base):
    __tablename__ = "matricula"
    __table_args__ = (
        CheckConstraint("fim >= inicio", name="ck_matricula_periodo"),
        CheckConstraint("estado IN ('ATIVA', 'ENCERRADA')", name="ck_matricula_estado"),
        CheckConstraint(
            "btrim(modalidade_contratada) <> ''", name="ck_matricula_modalidade"
        ),
        CheckConstraint(
            """jsonb_typeof(limites_snapshot) = 'object'
            AND limites_snapshot ?& array['limite_acessos', 'janela_limite']
            AND CASE jsonb_typeof(limites_snapshot -> 'limite_acessos')
                WHEN 'null' THEN limites_snapshot -> 'janela_limite' = 'null'::jsonb
                WHEN 'number' THEN
                    limites_snapshot ->> 'limite_acessos' ~ '^[1-9][0-9]*$'
                    AND limites_snapshot -> 'janela_limite' = '"DIA_CIVIL"'::jsonb
                ELSE false END""",
            name="ck_matricula_limites",
        ),
        UniqueConstraint("id", "cliente_id", name="uq_matricula_cliente_id"),
        Index("ix_matricula_cliente_periodo", "cliente_id", "inicio", "fim"),
        Index("ix_matricula_plano", "plano_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("academia.cliente.usuario_id"))
    plano_id: Mapped[UUID] = mapped_column(ForeignKey("academia.plano.id"))
    atendente_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.funcionario.usuario_id")
    )
    inicio: Mapped[date]
    fim: Mapped[date]
    estado: Mapped[MembershipState] = mapped_column(String(20))
    modalidade_contratada: Mapped[str] = mapped_column(String(80))
    limites_snapshot: Mapped[dict[str, int | str | None]] = mapped_column(JSONB)

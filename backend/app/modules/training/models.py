from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Exercise(Base):
    __tablename__ = "exercicio"
    __table_args__ = (
        UniqueConstraint("nome_normalizado", name="uq_exercicio_nome_normalizado"),
        CheckConstraint(
            "length(btrim(nome_normalizado)) > 0 AND length(btrim(nome)) > 0 "
            "AND length(btrim(descricao)) > 0 AND length(btrim(grupo_muscular)) > 0",
            name="ck_exercicio_textos",
        ),
        CheckConstraint("revision >= 1", name="ck_exercicio_revisao"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    nome_normalizado: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text)
    grupo_muscular: Mapped[str] = mapped_column(String(80))
    dispensa_equipamento: Mapped[bool]
    ativo: Mapped[bool]
    revision: Mapped[int]
    grupos: Mapped[list[ExerciseResourceGroup]] = relationship(
        cascade="all, delete-orphan", order_by="ExerciseResourceGroup.id"
    )


class ExerciseResourceGroup(Base):
    __tablename__ = "exercicio_recurso_grupo"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    exercicio_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.exercicio.id", ondelete="CASCADE"), index=True
    )
    recursos: Mapped[list[ExerciseResource]] = relationship(
        cascade="all, delete-orphan", order_by="ExerciseResource.equipamento_id"
    )


class ExerciseResource(Base):
    __tablename__ = "exercicio_recurso"
    __table_args__ = (
        UniqueConstraint(
            "grupo_id", "equipamento_id", name="uq_exercicio_recurso_grupo"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    grupo_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.exercicio_recurso_grupo.id", ondelete="CASCADE")
    )
    equipamento_id: Mapped[UUID] = mapped_column(ForeignKey("academia.equipamento.id"))

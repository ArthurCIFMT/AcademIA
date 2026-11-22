from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ClientProfile(Base):
    __tablename__ = "cliente"
    __table_args__ = (
        CheckConstraint("cpf ~ '^[0-9]{11}$'", name="ck_cliente_cpf_formato"),
        UniqueConstraint("cpf", name="uq_cliente_cpf"),
    )

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.usuario.id"), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(120))
    data_nascimento: Mapped[date]
    telefone: Mapped[str | None] = mapped_column(String(25))
    cpf: Mapped[str | None] = mapped_column(String(11))
    ativo: Mapped[bool]


class EmployeeProfile(Base):
    __tablename__ = "funcionario"

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.usuario.id"), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(120))
    cargo: Mapped[str] = mapped_column(String(80))
    data_admissao: Mapped[date]
    ativo: Mapped[bool]

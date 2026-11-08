from datetime import date
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ClientProfile(Base):
    __tablename__ = "cliente"

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("academia.usuario.id"), primary_key=True
    )
    nome: Mapped[str] = mapped_column(String(120))
    data_nascimento: Mapped[date]
    telefone: Mapped[str | None] = mapped_column(String(25))
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

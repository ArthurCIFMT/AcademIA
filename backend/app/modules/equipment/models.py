from uuid import UUID

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Equipment(Base):
    __tablename__ = "equipamento"
    __table_args__ = (
        CheckConstraint("length(btrim(nome)) > 0", name="ck_equipamento_nome"),
        CheckConstraint("revision >= 1", name="ck_equipamento_revisao"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(Text)
    categoria: Mapped[str | None] = mapped_column(String(80))
    imagem_ref: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool]
    operacional: Mapped[bool]
    revision: Mapped[int]

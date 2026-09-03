from datetime import date

from sqlalchemy import BigInteger, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from .session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    position: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        return f"{self.due_date.strftime('%d %B')} — {self.label}"

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="resident")
    source: Mapped[str] = mapped_column(String(10), default="orion")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    homes: Mapped[list["Home"]] = relationship(back_populates="user")

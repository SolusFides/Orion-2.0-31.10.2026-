from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class Home(Base):
    __tablename__ = "homes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(10), default="manual")
    mode: Mapped[str] = mapped_column(String(10), default="home")
    ujin_apartment_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="homes")
    rooms: Mapped[list["Room"]] = relationship(
        back_populates="home", cascade="all, delete-orphan", order_by="Room.sort"
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="home", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        back_populates="home", cascade="all, delete-orphan"
    )


class RoomType(Base):
    __tablename__ = "room_types"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(30))
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_type_code: Mapped[str] = mapped_column(ForeignKey("room_types.code"))
    title: Mapped[str] = mapped_column(String(50))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    home: Mapped[Home] = relationship(back_populates="rooms")
    room_type: Mapped[RoomType] = relationship()
    devices: Mapped[list["Device"]] = relationship(back_populates="room")

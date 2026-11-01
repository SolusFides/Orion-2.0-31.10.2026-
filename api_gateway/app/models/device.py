from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class DeviceType(Base):
    __tablename__ = "device_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(100))
    family: Mapped[str | None] = mapped_column(String(30))
    icon: Mapped[str] = mapped_column(String(30), default="device")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    declaration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    buy_url: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"), index=True)
    device_type_id: Mapped[int] = mapped_column(ForeignKey("device_types.id"))
    title: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(10), default="virtual")
    online: Mapped[bool] = mapped_column(Boolean, default=True)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ujin_serial: Mapped[str | None] = mapped_column(String(30))
    ujin_ext_guid: Mapped[str | None] = mapped_column(String(60))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)

    home: Mapped["Home"] = relationship(back_populates="devices")
    room: Mapped["Room"] = relationship(back_populates="devices")
    device_type: Mapped[DeviceType] = relationship()


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int | None] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(50))
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    prev_value: Mapped[Any] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(10))
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    run_step_id: Mapped[int | None] = mapped_column(ForeignKey("run_steps.id", ondelete="SET NULL"))
    signal: Mapped[str] = mapped_column(String(50))
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10), default="sent")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

from typing import Any, Literal

from pydantic import BaseModel, Field

HomeMode = Literal["home", "away", "night"]


class UserOut(BaseModel):
    id: int
    name: str
    role: str
    source: str


class HomeRef(BaseModel):
    id: int
    title: str


class MeOut(BaseModel):
    user: UserOut
    home: HomeRef | None


class RoomTypeOut(BaseModel):
    code: str
    title: str
    icon: str


class RoomIn(BaseModel):
    type: str
    title: str | None = Field(None, max_length=50)


class HomeCreate(BaseModel):
    title: str = Field("Моя квартира", min_length=1, max_length=100)
    address: str | None = Field(None, max_length=200)
    rooms: list[RoomIn] = Field(default_factory=list)


class HomePatch(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    mode: HomeMode | None = None


class RoomPatch(BaseModel):
    title: str = Field(min_length=1, max_length=50)


class DeviceSummary(BaseModel):
    signal: str
    value: Any
    text: str | None = None
    level: Literal["ok", "warning", "alarm"] = "ok"


class DeviceBrief(BaseModel):
    id: int
    title: str
    type: str
    icon: str
    mode: str
    online: bool
    summary: DeviceSummary | None


class RoomOut(BaseModel):
    id: int
    type: str
    title: str
    devices: list[DeviceBrief]
    scenarios_count: int


class Health(BaseModel):
    devices_total: int
    offline: int
    low_battery: int


class ScenarioBrief(BaseModel):
    id: int
    title: str
    description: str
    enabled: bool
    source: str
    last_run: str | None


class HomeShort(BaseModel):
    id: int
    title: str
    address: str | None
    source: str
    mode: HomeMode


class HomeOut(HomeShort):
    health: Health
    rooms: list[RoomOut]
    unassigned_devices: list[DeviceBrief]
    scenarios: list[ScenarioBrief]
    unread_notifications: int


class RoomDetail(RoomOut):
    home_id: int
    scenarios: list[ScenarioBrief]

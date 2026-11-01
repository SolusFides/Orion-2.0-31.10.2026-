from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalsCount(BaseModel):
    property: int
    capability: int
    setting: int


class DeviceTypeOut(BaseModel):
    id: int
    code: str
    title: str
    family: str | None
    icon: str
    is_custom: bool
    signals_count: SignalsCount
    events_count: int
    buy_url: str | None


class DeviceCreate(BaseModel):
    home_id: int | None = None
    room_id: int | None = None
    device_type_id: int
    title: str | None = Field(None, max_length=100)


class DevicePatch(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    room_id: int | None = None
    unassign: bool = False


class SignalValue(BaseModel):
    name: str
    title: str
    control: str
    management: str
    value: Any = None
    text: str | None = None
    unit: str | None = None
    min: float | None = None
    max: float | None = None
    values: list[dict[str, Any]] | None = None


class Groups(BaseModel):
    property: list[SignalValue]
    capability: list[SignalValue]
    setting: list[SignalValue]


class NamedRef(BaseModel):
    name: str
    title: str


class RoomRef(BaseModel):
    id: int
    title: str


class TypeRef(BaseModel):
    id: int
    code: str
    title: str
    icon: str


class DeviceScenarioRef(BaseModel):
    id: int
    title: str
    role: str


class UjinRef(BaseModel):
    linked: bool
    ext_guid: str | None


class DeviceOut(BaseModel):
    id: int
    home_id: int
    title: str
    room: RoomRef | None
    type: TypeRef
    mode: str
    online: bool
    last_seen_at: str | None
    groups: Groups
    events: list[NamedRef]
    scenarios: list[DeviceScenarioRef]
    buy_url: str | None
    ujin: UjinRef


class CommandIn(BaseModel):
    signal: str
    value: Any


class CommandOut(BaseModel):
    id: int
    signal: str
    value: Any
    source: str
    status: str
    error: str | None
    ms: int | None
    created_at: str


class CommandResult(BaseModel):
    command: CommandOut
    state: dict[str, Any]


class SimulateIn(BaseModel):
    signal: str
    value: Any


class SimulateOut(BaseModel):
    event_id: int | None
    state: dict[str, Any]
    triggered_runs: list[int] = Field(default_factory=list)


class OnlineIn(BaseModel):
    online: bool


class OnlineOut(BaseModel):
    device_id: int
    online: bool


def ms_between(a: datetime | None, b: datetime | None) -> int | None:
    if a is None or b is None:
        return None
    return int((b - a).total_seconds() * 1000)


class ValueText(BaseModel):
    value: Any
    text: str = Field(min_length=1, max_length=50)


class SignalDecl(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
    title: str = Field(min_length=1, max_length=60)
    group: str = Field(pattern=r"^(property|capability|setting)$")
    control: str = Field(pattern=r"^(switch|range|list|graph|counter|text|button)$")
    management: str = Field(pattern=r"^(r|rw|w)$")
    unit: str | None = Field(None, max_length=20)
    min: float | None = None
    max: float | None = None
    values: list[ValueText] | None = None
    summary: bool | None = None
    alarm_values: list[Any] | None = None


class EventWhen(BaseModel):
    signal: str
    op: str = Field("==", pattern=r"^(==|!=|>|>=|<|<=)$")
    value: Any


class EventDecl(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
    title: str = Field(min_length=1, max_length=60)
    when: EventWhen


class Declaration(BaseModel):
    signals: list[SignalDecl] = Field(min_length=1)
    events: list[EventDecl] = Field(default_factory=list)


class DeviceTypeIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    icon: str = Field("device", max_length=30)
    buy_url: str | None = Field(None, max_length=300)
    declaration: Declaration


class DeviceTypeDetail(DeviceTypeOut):
    declaration: dict[str, Any]


class CloneIn(BaseModel):
    title: str | None = Field(None, max_length=100)

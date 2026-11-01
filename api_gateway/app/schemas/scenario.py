from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

Op = Literal["==", "!=", ">", ">=", "<", "<="]
Mode = Literal["home", "away", "night"]


class RoomRef(BaseModel):
    id: int
    title: str


class TemplateUse(BaseModel):
    role: str
    title: str
    type: str
    device_id: int
    device_title: str
    room: str | None


class TemplateMissing(BaseModel):
    role: str
    title: str
    type: str
    buy_url: str | None


class TemplateOut(BaseModel):
    id: int
    code: str
    title: str
    description: str
    room_types: list[str]
    rooms: list[RoomRef]
    ready: bool
    uses: list[TemplateUse]
    missing: list[TemplateMissing]


class FromTemplateIn(BaseModel):
    home_id: int
    template_id: int
    room_id: int | None = None
    add_virtual_missing: bool = False


class ScenarioOut(BaseModel):
    id: int
    home_id: int
    title: str
    description: str
    enabled: bool
    source: str
    template_id: int | None
    cooldown_s: int
    conditions: list[dict[str, Any]]
    logic: str
    actions: list[dict[str, Any]]
    on_error: dict[str, Any]
    last_run: str | None = None


class FromTemplateOut(BaseModel):
    scenario: ScenarioOut
    created_devices: list[int]


class StateCondition(BaseModel):
    type: Literal["state"]
    device_id: int
    signal: str
    op: Op = "=="
    value: Any


class EventCondition(BaseModel):
    type: Literal["event"]
    device_id: int
    event: str


class ModeCondition(BaseModel):
    type: Literal["mode"]
    op: Literal["==", "!="] = "=="
    value: Mode


class TimeCondition(BaseModel):
    type: Literal["time"]
    op: Op = ">="
    value: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


Condition = Annotated[Union[StateCondition, EventCondition, ModeCondition, TimeCondition], Field(discriminator="type")]


class CommandAction(BaseModel):
    type: Literal["command"]
    device_id: int
    signal: str
    value: Any


class NotifyAction(BaseModel):
    type: Literal["notify"]
    audience: Literal["resident", "concierge"] = "resident"
    level: Literal["info", "warning", "alarm"] = "info"
    text: str = Field(min_length=1, max_length=500)


class DelayAction(BaseModel):
    type: Literal["delay"]
    seconds: int = Field(ge=1, le=3600)


Action = Annotated[Union[CommandAction, NotifyAction, DelayAction], Field(discriminator="type")]


class OnError(BaseModel):
    retries: int = Field(3, ge=0, le=5)
    retry_delay_s: float = Field(2, ge=0, le=30)
    timeout_s: float = Field(3, ge=0.5, le=30)
    fallback: list[NotifyAction] = Field(default_factory=list)


class ScenarioBody(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    enabled: bool = True
    conditions: list[Condition] = Field(min_length=1)
    logic: Literal["and", "or"] = "and"
    actions: list[Action] = Field(min_length=1)
    on_error: OnError | None = None
    cooldown_s: int = Field(60, ge=0, le=86400)


class ScenarioCreate(ScenarioBody):
    home_id: int


class ScenarioValidateIn(ScenarioBody):
    home_id: int
    scenario_id: int | None = None


class ScenarioPatch(BaseModel):
    enabled: bool | None = None
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class Issue(BaseModel):
    path: str
    code: str
    message: str
    scenario_id: int | None = None


class ValidateOut(BaseModel):
    ok: bool
    errors: list[Issue]
    warnings: list[Issue]


class CatalogSignal(BaseModel):
    name: str
    title: str
    control: str
    unit: str | None = None
    min: float | None = None
    max: float | None = None
    values: list[dict[str, Any]] | None = None


class CatalogDevice(BaseModel):
    id: int
    title: str
    room: str | None
    type: str
    icon: str
    online: bool
    states: list[CatalogSignal]
    events: list[dict[str, str]]
    commands: list[CatalogSignal]


class Choice(BaseModel):
    value: str
    title: str


class EditorCatalog(BaseModel):
    devices: list[CatalogDevice]
    condition_types: list[Choice]
    action_types: list[Choice]
    ops: list[str]
    modes: list[Choice]
    audiences: list[Choice]
    levels: list[Choice]

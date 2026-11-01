from typing import Any

from pydantic import BaseModel, Field

from app.schemas.scenario import ScenarioOut


class AssistantIn(BaseModel):
    home_id: int
    session_id: int | None = None
    text: str = Field(min_length=1, max_length=500)


class MessageOut(BaseModel):
    id: int
    role: str
    text: str
    proposal: dict[str, Any] | None = None
    engine: str | None = None
    created_at: str | None


class AssistantReply(BaseModel):
    session_id: int
    message: MessageOut
    proposal: dict[str, Any] | None = None
    suggestions: list[str]


class SessionOut(BaseModel):
    id: int
    home_id: int
    messages: list[MessageOut]


class AcceptIn(BaseModel):
    add_virtual_missing: bool = True
    room_id: int | None = None
    edit: bool = False


class AcceptOut(BaseModel):
    scenario: ScenarioOut | None = None
    created_devices: list[int] = Field(default_factory=list)
    draft: dict[str, Any] | None = None

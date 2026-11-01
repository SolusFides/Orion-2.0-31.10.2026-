from pydantic import BaseModel


class HomeBrief(BaseModel):
    id: int
    title: str
    address: str | None


class NotificationOut(BaseModel):
    id: int
    home: HomeBrief
    run_id: int | None
    audience: str
    level: str
    title: str
    text: str
    status: str
    created_at: str | None

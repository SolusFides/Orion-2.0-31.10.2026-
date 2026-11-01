from pydantic import BaseModel


class JournalItem(BaseModel):
    kind: str
    at: str | None
    title: str
    text: str | None = None
    level: str
    run_id: int | None = None
    device_id: int | None = None
    status: str | None = None
    audience: str | None = None

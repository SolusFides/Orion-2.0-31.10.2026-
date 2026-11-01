from typing import Any

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    db: str
    engine: str
    emulator: dict[str, Any]
    ujin: dict[str, Any]


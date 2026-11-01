from pydantic import BaseModel


class ScenarioRef(BaseModel):
    id: int
    title: str


class RunTrigger(BaseModel):
    device: str | None
    what: str
    at: str | None


class RunStepOut(BaseModel):
    idx: int
    type: str
    title: str
    status: str
    attempts: int
    error: str | None
    at: str | None


class RunBrief(BaseModel):
    id: int
    scenario: ScenarioRef
    status: str
    dry_run: bool
    reason: str | None
    started_at: str | None
    finished_at: str | None


class RunOut(RunBrief):
    trigger: RunTrigger | None
    steps: list[RunStepOut]


class RunStarted(BaseModel):
    run_id: int

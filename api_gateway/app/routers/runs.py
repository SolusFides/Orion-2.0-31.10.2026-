from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUser
from app.repositories.journal import JournalRepository
from app.repositories.run import RunRepository
from app.schemas import run as schemas
from app.schemas.journal import JournalItem
from app.services.engine import engine

router = APIRouter(prefix="/api", tags=["Runs"])
repo = RunRepository()
journal_repo = JournalRepository()


@router.get("/homes/{home_id}/runs", response_model=list[schemas.RunBrief])
async def home_runs(home_id: int, user: CurrentUser, limit: int = Query(50, ge=1, le=200),
                    dry: bool = Query(False)) -> list[schemas.RunBrief]:
    return await repo.list_for_home(home_id, user.id, limit, dry)


@router.get("/scenarios/{scenario_id}/runs", response_model=list[schemas.RunBrief])
async def scenario_runs(scenario_id: int, user: CurrentUser,
                        limit: int = Query(50, ge=1, le=200)) -> list[schemas.RunBrief]:
    return await repo.list_for_scenario(scenario_id, user.id, limit)


@router.get("/runs/{run_id}", response_model=schemas.RunOut)
async def get_run(run_id: int, user: CurrentUser) -> schemas.RunOut:
    return await repo.get(run_id, user.id)


@router.post("/scenarios/{scenario_id}/test", response_model=schemas.RunOut)
async def test_scenario(scenario_id: int, user: CurrentUser) -> schemas.RunOut:
    await repo.scenario_home(scenario_id, user.id)
    run_id = await engine.run_now(scenario_id, dry_run=True)
    return await repo.get(run_id, user.id)


@router.post("/scenarios/{scenario_id}/run", response_model=schemas.RunStarted,
             status_code=status.HTTP_202_ACCEPTED)
async def run_scenario(scenario_id: int, user: CurrentUser) -> schemas.RunStarted:
    await repo.scenario_home(scenario_id, user.id)
    return schemas.RunStarted(run_id=await engine.run_now(scenario_id))


@router.get("/homes/{home_id}/journal", response_model=list[JournalItem])
async def home_journal(home_id: int, user: CurrentUser, limit: int = Query(50, ge=1, le=200)) -> list[JournalItem]:
    return await journal_repo.for_home(home_id, user.id, limit)

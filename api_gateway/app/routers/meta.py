from fastapi import APIRouter
from sqlalchemy import text

from app.database import session_manager
from app.dependencies.auth import CurrentUser
from app.repositories.home import HomeRepository
from app.repositories.room_type import RoomTypeRepository
from app.schemas import home as schemas
from app.schemas.common import HealthOut
from app.services.emulator import emulator
from app.services.engine import engine
from app.services.ujin import publisher

router = APIRouter(prefix="/api", tags=["Me"])
home_repo = HomeRepository()
room_type_repo = RoomTypeRepository()


@router.get("/me", response_model=schemas.MeOut)
async def me(user: CurrentUser) -> schemas.MeOut:
    home = await home_repo.latest_for_user(user.id)
    return schemas.MeOut(
        user=schemas.UserOut(id=user.id, name=user.name, role=user.role, source=user.source),
        home=schemas.HomeRef(id=home.id, title=home.title) if home else None,
    )


@router.get("/room-types", response_model=list[schemas.RoomTypeOut])
async def room_types() -> list[schemas.RoomTypeOut]:
    return [schemas.RoomTypeOut(code=r.code, title=r.title, icon=r.icon) for r in await room_type_repo.list()]


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    try:
        async with session_manager() as session:
            await session.execute(text("SELECT 1"))
        db = "ok"
    except Exception:
        db = "error"
    ujin = publisher.status()
    return HealthOut(status="ok" if db == "ok" else "degraded", db=db,
                     engine=f"ok: {len(engine.last_truth)} сценариев", emulator=emulator.status(),
                     ujin={"enabled": ujin["enabled"], "connected": ujin["connected"]})


@router.get("/emulator/status")
async def emulator_status(_: CurrentUser) -> dict:
    return emulator.status()

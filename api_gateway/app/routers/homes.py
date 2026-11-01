from fastapi import APIRouter, Request, Response, status

from app.dependencies.auth import CurrentUser, StreamUser
from app.repositories.home import HomeRepository
from app.schemas import home as schemas
from app.services.engine import Change, engine
from app.services.errors import not_found
from app.services.sse import home_channel, hub

router = APIRouter(prefix="/api", tags=["Homes"])
repo = HomeRepository()


@router.post("/homes", response_model=schemas.HomeOut, status_code=status.HTTP_201_CREATED)
async def create_home(body: schemas.HomeCreate, user: CurrentUser) -> schemas.HomeOut:
    return await repo.create(user.id, body)


@router.get("/homes/{home_id}", response_model=schemas.HomeOut)
async def get_home(home_id: int, user: CurrentUser) -> schemas.HomeOut:
    return await repo.detail(home_id, user.id)


@router.patch("/homes/{home_id}", response_model=schemas.HomeShort)
async def patch_home(home_id: int, body: schemas.HomePatch, user: CurrentUser) -> schemas.HomeShort:
    home, old_mode, event_id = await repo.patch(home_id, user.id, body)
    if home.mode != old_mode:
        hub.publish(home_channel(home.id), "home_mode", {"home_id": home.id, "mode": home.mode, "prev": old_mode})
        await engine.on_change(Change(home_id=home.id, kind="mode", event_id=event_id))
    return home


@router.post("/homes/{home_id}/rooms", response_model=schemas.RoomDetail, status_code=status.HTTP_201_CREATED)
async def add_room(home_id: int, body: schemas.RoomIn, user: CurrentUser) -> schemas.RoomDetail:
    return await repo.add_room(home_id, user.id, body)


@router.get("/rooms/{room_id}", response_model=schemas.RoomDetail)
async def get_room(room_id: int, user: CurrentUser) -> schemas.RoomDetail:
    return await repo.room(room_id, user.id)


@router.patch("/rooms/{room_id}", response_model=schemas.RoomDetail)
async def patch_room(room_id: int, body: schemas.RoomPatch, user: CurrentUser) -> schemas.RoomDetail:
    return await repo.rename_room(room_id, user.id, body)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: int, user: CurrentUser) -> Response:
    await repo.delete_room(room_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/homes/{home_id}/stream")
async def home_stream(home_id: int, request: Request, user: StreamUser):
    if not await repo.exists_for_user(home_id, user.id):
        raise not_found("Дом", home_id)
    return hub.response(home_channel(home_id), request)

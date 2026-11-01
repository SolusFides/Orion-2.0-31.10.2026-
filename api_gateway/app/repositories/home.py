from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import session_manager
from app.models import Device, Event, Home, Notification, Room, RoomType, Run
from app.schemas import home as schemas
from app.services import homes as views
from app.services.errors import ApiError, not_found


async def _load_home(session: AsyncSession, home_id: int, user_id: int) -> Home:
    home = await session.scalar(
        select(Home)
        .where(Home.id == home_id)
        .options(
            selectinload(Home.rooms),
            selectinload(Home.devices).selectinload(Device.device_type),
            selectinload(Home.scenarios),
        )
    )
    if home is None or home.user_id != user_id:
        raise not_found("Дом", home_id)
    return home


async def _last_runs(session: AsyncSession, scenario_ids: list[int]) -> dict[int, str]:
    if not scenario_ids:
        return {}
    last = (
        select(Run.scenario_id, func.max(Run.id).label("rid"))
        .where(Run.scenario_id.in_(scenario_ids), Run.dry_run.is_(False))
        .group_by(Run.scenario_id)
        .subquery()
    )
    rows = await session.execute(select(Run.scenario_id, Run.status).join(last, Run.id == last.c.rid))
    return {sid: status for sid, status in rows.all()}


async def _room_type(session: AsyncSession, code: str) -> RoomType:
    rt = await session.get(RoomType, code)
    if rt is None:
        raise ApiError(422, "validation_error", f"Нет типа комнаты «{code}»", {"type": code})
    return rt


async def _detail(session: AsyncSession, home_id: int, user_id: int) -> schemas.HomeOut:
    home = await _load_home(session, home_id, user_id)
    last = await _last_runs(session, [s.id for s in home.scenarios])
    unread = await session.scalar(
        select(func.count(Notification.id)).where(
            Notification.home_id == home.id, Notification.audience == "resident", Notification.status == "new"
        )
    )
    return views.home_detail(home, last, unread or 0)


async def _room_detail(session: AsyncSession, room_id: int, user_id: int) -> schemas.RoomDetail:
    room = await session.get(Room, room_id)
    if room is None:
        raise not_found("Комната", room_id)
    try:
        home = await _load_home(session, room.home_id, user_id)
    except ApiError:
        raise not_found("Комната", room_id) from None
    last = await _last_runs(session, [s.id for s in home.scenarios])
    return views.room_detail(home, room, last)


class HomeRepository:
    async def latest_for_user(self, user_id: int) -> Home | None:
        async with session_manager() as session:
            return await session.scalar(
                select(Home).where(Home.user_id == user_id).order_by(Home.id.desc()).limit(1)
            )

    async def create(self, user_id: int, data: schemas.HomeCreate) -> schemas.HomeOut:
        async with session_manager() as session:
            home = Home(user_id=user_id, title=data.title, address=data.address, source="manual")
            for sort, r in enumerate(data.rooms):
                rt = await _room_type(session, r.type)
                home.rooms.append(Room(room_type_code=rt.code, title=r.title or rt.title, sort=sort))
            session.add(home)
            await session.commit()
            return await _detail(session, home.id, user_id)

    async def detail(self, home_id: int, user_id: int) -> schemas.HomeOut:
        async with session_manager() as session:
            return await _detail(session, home_id, user_id)

    async def patch(self, home_id: int, user_id: int, data: schemas.HomePatch
                    ) -> tuple[schemas.HomeShort, str, int | None]:
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            old_mode = home.mode
            if data.title is not None:
                home.title = data.title
            event_id = None
            if data.mode is not None and data.mode != old_mode:
                home.mode = data.mode
                ev = Event(home_id=home.id, device_id=None, kind="mode", name="mode", value=data.mode,
                           prev_value=old_mode, source="user")
                session.add(ev)
                await session.flush()
                event_id = ev.id
            await session.commit()
            return views.home_short(home), old_mode, event_id

    async def add_room(self, home_id: int, user_id: int, data: schemas.RoomIn) -> schemas.RoomDetail:
        async with session_manager() as session:
            await _load_home(session, home_id, user_id)
            rt = await _room_type(session, data.type)
            max_sort = await session.scalar(select(func.max(Room.sort)).where(Room.home_id == home_id))
            next_sort = 0 if max_sort is None else max_sort + 1
            room = Room(home_id=home_id, room_type_code=rt.code, title=data.title or rt.title, sort=next_sort)
            session.add(room)
            await session.commit()
            return await _room_detail(session, room.id, user_id)

    async def room(self, room_id: int, user_id: int) -> schemas.RoomDetail:
        async with session_manager() as session:
            return await _room_detail(session, room_id, user_id)

    async def rename_room(self, room_id: int, user_id: int, data: schemas.RoomPatch) -> schemas.RoomDetail:
        async with session_manager() as session:
            await _room_detail(session, room_id, user_id)
            room = await session.get(Room, room_id)
            room.title = data.title
            await session.commit()
            return await _room_detail(session, room_id, user_id)

    async def delete_room(self, room_id: int, user_id: int) -> None:
        async with session_manager() as session:
            await _room_detail(session, room_id, user_id)
            for d in await session.scalars(select(Device).where(Device.room_id == room_id)):
                d.room_id = None
            await session.delete(await session.get(Room, room_id))
            await session.commit()

    async def exists_for_user(self, home_id: int, user_id: int) -> bool:
        async with session_manager() as session:
            home = await session.get(Home, home_id)
            return home is not None and home.user_id == user_id

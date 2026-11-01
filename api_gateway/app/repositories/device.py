import re
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import iso, session_manager, utcnow
from app.models import Device, DeviceCommand, DeviceType, Event, Home, Room, Scenario
from app.schemas import device as schemas
from app.services import declaration as decl_svc
from app.services import devices as dev
from app.services.engine import Change, engine
from app.services.errors import ApiError, not_found
from app.services.sse import home_channel, hub
from app.services.state import apply_with_physics, state_lock

async def _load_device(session: AsyncSession, device_id: int, user_id: int) -> Device:
    device = await session.scalar(
        select(Device).where(Device.id == device_id)
        .options(selectinload(Device.device_type), selectinload(Device.room))
    )
    if device is None:
        raise not_found("Устройство", device_id)
    home = await session.get(Home, device.home_id)
    if home is None or home.user_id != user_id:
        raise not_found("Устройство", device_id)
    return device


async def _home_scenarios(session: AsyncSession, home_id: int) -> list[Scenario]:
    return list(await session.scalars(select(Scenario).where(Scenario.home_id == home_id)))


def _command_out(c: DeviceCommand) -> schemas.CommandOut:
    return schemas.CommandOut(id=c.id, signal=c.signal, value=c.value, source=c.source, status=c.status,
                              error=c.error, ms=schemas.ms_between(c.created_at, c.finished_at),
                              created_at=iso(c.created_at))


class DeviceRepository:
    async def list_types(self) -> list[schemas.DeviceTypeOut]:
        async with session_manager() as session:
            types = await session.scalars(select(DeviceType).order_by(DeviceType.is_custom, DeviceType.id))
            return [dev.device_type_out(t) for t in types]

    async def get(self, device_id: int, user_id: int) -> schemas.DeviceOut:
        async with session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            return dev.device_out(device, await _home_scenarios(session, device.home_id))

    async def create(self, user_id: int, body: schemas.DeviceCreate) -> schemas.DeviceOut:
        async with session_manager() as session:
            room = None
            if body.room_id is not None:
                room = await session.get(Room, body.room_id)
                if room is None:
                    raise not_found("Комната", body.room_id)
            home_id = room.home_id if room else body.home_id
            if home_id is None:
                raise ApiError(422, "validation_error", "Нужна комната (room_id) или дом (home_id)")
            home = await session.get(Home, home_id)
            if home is None or home.user_id != user_id:
                raise not_found("Дом", home_id)
            dtype = await session.get(DeviceType, body.device_type_id)
            if dtype is None:
                raise not_found("Тип устройства", body.device_type_id)
            device = Device(home_id=home.id, room_id=room.id if room else None, device_type_id=dtype.id,
                            title=body.title or dtype.title, mode="virtual", online=True,
                            state=dict((dtype.declaration or {}).get("defaults", {})))
            session.add(device)
            await session.commit()
            device = await _load_device(session, device.id, user_id)
            return dev.device_out(device, [])

    async def patch(self, device_id: int, user_id: int, body: schemas.DevicePatch) -> schemas.DeviceOut:
        async with session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            if body.title is not None:
                device.title = body.title
            if body.unassign:
                device.room_id = None
            elif body.room_id is not None:
                room = await session.get(Room, body.room_id)
                if room is None or room.home_id != device.home_id:
                    raise not_found("Комната", body.room_id)
                device.room_id = room.id
            await session.commit()
            device = await _load_device(session, device_id, user_id)
            return dev.device_out(device, await _home_scenarios(session, device.home_id))

    async def delete(self, device_id: int, user_id: int) -> list[int]:
        async with session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            disabled = []
            for s in await _home_scenarios(session, device.home_id):
                if any(p.get("device_id") == device.id for p in [*s.conditions, *s.actions]) and s.enabled:
                    s.enabled = False
                    disabled.append(s.id)
            await session.delete(device)
            await session.commit()
            return disabled

    async def command(self, device_id: int, user_id: int, body: schemas.CommandIn) -> schemas.CommandResult:
        async with state_lock, session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            sig = dev.find_signal(device.device_type, body.signal)
            if sig is None:
                raise ApiError(422, "validation_error", f"У «{device.title}» нет команды «{body.signal}»")
            if not dev.writable(sig):
                raise ApiError(422, "signal_readonly", f"«{sig['title']}» только для чтения")
            if problem := dev.check_value(sig, body.value):
                raise ApiError(422, *problem)
            cmd = DeviceCommand(device_id=device.id, signal=body.signal, value=body.value, source="user")
            session.add(cmd)
            if not device.online:
                cmd.status, cmd.error, cmd.finished_at = "failed", "device_offline", utcnow()
                await session.commit()
                raise ApiError(409, "device_offline", f"«{device.title}» не в сети", {"command_id": cmd.id})
            ev, fired = apply_with_physics(session, device, body.signal, body.value, "command",
                                           write_state=sig.get("management") == "rw")
            await session.flush()
            change = Change(home_id=device.home_id, device_id=device.id, events=fired,
                            event_id=ev.id if ev else None)
            cmd.status, cmd.finished_at = "ok", utcnow()
            await session.commit()
            result = schemas.CommandResult(command=_command_out(cmd), state=device.state)
        await engine.on_change(change)
        return result

    async def commands(self, device_id: int, user_id: int, limit: int = 50) -> list[schemas.CommandOut]:
        async with session_manager() as session:
            await _load_device(session, device_id, user_id)
            rows = await session.scalars(
                select(DeviceCommand).where(DeviceCommand.device_id == device_id)
                .order_by(DeviceCommand.id.desc()).limit(limit)
            )
            return [_command_out(c) for c in rows]

    async def simulate(self, device_id: int, user_id: int, body: schemas.SimulateIn) -> schemas.SimulateOut:
        async with state_lock, session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            sig = dev.find_signal(device.device_type, body.signal)
            if sig is None:
                raise ApiError(422, "validation_error", f"У «{device.title}» нет сигнала «{body.signal}»")
            if not device.online:
                raise ApiError(409, "device_offline", f"«{device.title}» не в сети — сначала верните связь")
            if problem := dev.check_value(sig, body.value):
                raise ApiError(422, *problem)
            ev, fired = apply_with_physics(session, device, body.signal, body.value, "simulate",
                                           write_state=sig.get("management") != "w")
            await session.flush()
            change = Change(home_id=device.home_id, device_id=device.id, events=fired,
                            event_id=ev.id if ev else None)
            await session.commit()
            state = dict(device.state)
        runs = await engine.on_change(change)
        return schemas.SimulateOut(event_id=change.event_id, state=state, triggered_runs=runs)

    async def set_online(self, device_id: int, user_id: int, online: bool) -> schemas.OnlineOut:
        async with state_lock, session_manager() as session:
            device = await _load_device(session, device_id, user_id)
            if device.online != online:
                device.online = online
                session.add(Event(home_id=device.home_id, device_id=device.id, kind="state", name="online",
                                  value=online, prev_value=not online, source="simulate"))
                hub.publish(home_channel(device.home_id), "device_online",
                            {"device_id": device.id, "online": online, "at": iso(utcnow())})
            await session.commit()
            return schemas.OnlineOut(device_id=device.id, online=device.online)


def _type_detail(t: DeviceType) -> schemas.DeviceTypeDetail:
    return schemas.DeviceTypeDetail(**dev.device_type_out(t).model_dump(), declaration=t.declaration or {})


def _check(decl: schemas.Declaration) -> dict:
    errors = decl_svc.problems(decl)
    if errors:
        raise ApiError(422, "validation_error", "Декларация не прошла проверку", {"errors": errors})
    data = decl.model_dump(exclude_none=True)
    data["defaults"] = decl_svc.defaults(data)
    return data


async def _custom_code(session: AsyncSession, title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "type"
    while True:
        code = f"custom_{base[:20]}_{secrets.token_hex(3)}"
        if await session.scalar(select(DeviceType.id).where(DeviceType.code == code)) is None:
            return code


class DeviceTypeRepository:
    async def get(self, type_id: int) -> schemas.DeviceTypeDetail:
        async with session_manager() as session:
            t = await session.get(DeviceType, type_id)
            if t is None:
                raise not_found("Тип устройства", type_id)
            return _type_detail(t)

    async def create(self, body: schemas.DeviceTypeIn) -> schemas.DeviceTypeDetail:
        async with session_manager() as session:
            t = DeviceType(code=await _custom_code(session, body.title), title=body.title, family=None,
                           icon=body.icon, is_custom=True, buy_url=body.buy_url, declaration=_check(body.declaration))
            session.add(t)
            await session.commit()
            return _type_detail(t)

    async def update(self, type_id: int, body: schemas.DeviceTypeIn) -> schemas.DeviceTypeDetail:
        async with session_manager() as session:
            t = await session.get(DeviceType, type_id)
            if t is None:
                raise not_found("Тип устройства", type_id)
            if not t.is_custom:
                raise ApiError(409, "not_custom", "Готовый тип менять нельзя — сделайте копию")
            used = await session.scalar(select(func.count(Device.id)).where(Device.device_type_id == type_id))
            if used:
                raise ApiError(409, "type_in_use", f"Тип используют устройства ({used}) — сделайте копию и меняйте её")
            t.title, t.icon, t.buy_url, t.declaration = body.title, body.icon, body.buy_url, _check(body.declaration)
            await session.commit()
            return _type_detail(t)

    async def delete(self, type_id: int) -> None:
        async with session_manager() as session:
            t = await session.get(DeviceType, type_id)
            if t is None:
                raise not_found("Тип устройства", type_id)
            if not t.is_custom:
                raise ApiError(409, "not_custom", "Готовый тип удалить нельзя")
            used = await session.scalar(select(func.count(Device.id)).where(Device.device_type_id == type_id))
            if used:
                raise ApiError(409, "type_in_use", f"Тип используют устройства: {used}")
            await session.delete(t)
            await session.commit()

    async def clone(self, type_id: int, body: schemas.CloneIn) -> schemas.DeviceTypeDetail:
        async with session_manager() as session:
            src = await session.get(DeviceType, type_id)
            if src is None:
                raise not_found("Тип устройства", type_id)
            title = body.title or f"{src.title} (копия)"
            t = DeviceType(code=await _custom_code(session, title), title=title, family=src.family, icon=src.icon,
                           is_custom=True, buy_url=src.buy_url, declaration=dict(src.declaration or {}))
            session.add(t)
            await session.commit()
            return _type_detail(t)

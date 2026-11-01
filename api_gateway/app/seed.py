import asyncio
import logging

from sqlalchemy import select

from app.config import settings
from app.database import session_manager
from sqlalchemy.orm import selectinload

from app.catalog import DEVICE_TYPES, HOME_SCENARIO_CODES, ROOM_TYPES, SCENARIO_TEMPLATES
from app.models import Device, DeviceType, Home, Room, RoomType, Scenario, ScenarioTemplate, User
from app.services import templates as tpl_svc
from app.services.security import hash_password, normalize_phone

log = logging.getLogger("seed")

UJIN_HOME_ROOMS = ["bathroom", "kitchen", "bedroom", "living"]
UJIN_HOME_DEVICES = [
    ("leak", "Датчик протечки", "orion_leak_01", "bathroom"),
    ("counter", "Счётчик холодной воды", "orion_counter_01", "kitchen"),
    ("thermostat", "Термостат", "orion_thermostat_01", "bedroom"),
    ("light", "Светильник", "orion_light_01", "living"),
    ("barrier", "Шлагбаум", "orion_barrier_01", None),
]


async def _seed_room_types(session) -> None:
    have = {rt.code: rt for rt in await session.scalars(select(RoomType))}
    for sort, rt in enumerate(ROOM_TYPES):
        row = have.get(rt["code"])
        if row is None:
            session.add(RoomType(sort=sort, **rt))
        else:
            row.title, row.icon, row.sort = rt["title"], rt["icon"], sort


async def _seed_device_types(session) -> dict[str, DeviceType]:
    have = {dt.code: dt for dt in await session.scalars(select(DeviceType))}
    for spec in DEVICE_TYPES:
        fields = {k: v for k, v in spec.items() if k != "initial"}
        fields["declaration"] = {**spec["declaration"], "defaults": spec["initial"]}
        row = have.get(spec["code"])
        if row is None:
            row = DeviceType(is_custom=False, **fields)
            session.add(row)
            have[spec["code"]] = row
        elif not row.is_custom:
            for k, v in fields.items():
                setattr(row, k, v)
    await session.flush()
    return have


async def _upsert_user(session, phone: str, password: str, name: str, source: str, role: str = "resident") -> User:
    phone = normalize_phone(phone)
    user = await session.scalar(select(User).where(User.phone == phone))
    if user is None:
        user = User(phone=phone, password_hash=hash_password(password), name=name, role=role, source=source)
        session.add(user)
        await session.flush()
        log.info("создан пользователь «%s»", name)
    return user


async def _seed_ujin_home(session, user: User, types: dict[str, DeviceType]) -> None:
    if await session.scalar(select(Home).where(Home.user_id == user.id)):
        return
    home = Home(user_id=user.id, title=f"Квартира {settings.UJIN_APARTMENT_ID}", address="Здание № 5/1, кв. 1",
                source="ujin", ujin_apartment_id=settings.UJIN_APARTMENT_ID)
    rooms: dict[str, Room] = {}
    by_code = {rt["code"]: rt for rt in ROOM_TYPES}
    for sort, code in enumerate(UJIN_HOME_ROOMS):
        rooms[code] = Room(room_type_code=code, title=by_code[code]["title"], sort=sort)
        home.rooms.append(rooms[code])
    session.add(home)
    await session.flush()
    initial = {spec["code"]: spec["initial"] for spec in DEVICE_TYPES}
    for type_code, title, ext_guid, room_code in UJIN_HOME_DEVICES:
        session.add(Device(
            home_id=home.id, room_id=rooms[room_code].id if room_code else None,
            device_type_id=types[type_code].id, title=title, mode="ujin", online=True,
            state=dict(initial[type_code]), ujin_ext_guid=ext_guid,
        ))
    log.info("создан дом «%s»: %d комнаты, %d устройств", home.title, len(rooms), len(UJIN_HOME_DEVICES))


async def _seed_home_scenarios(session, user: User) -> None:
    home = await session.scalar(
        select(Home).where(Home.user_id == user.id).order_by(Home.id).limit(1)
        .options(selectinload(Home.rooms), selectinload(Home.devices).selectinload(Device.device_type),
                 selectinload(Home.scenarios))
    )
    if home is None:
        return
    have = {s.template_id for s in home.scenarios}
    for code in HOME_SCENARIO_CODES:
        tpl = await session.scalar(select(ScenarioTemplate).where(ScenarioTemplate.code == code))
        if tpl is None or tpl.id in have:
            continue
        bindings, missing = tpl_svc.bind(home, tpl)
        if missing:
            continue
        session.add(Scenario(home_id=home.id, **tpl_svc.build_scenario(tpl, bindings, None)))
        log.info("создан сценарий дома «%s»", tpl.title)


async def _seed_templates(session) -> None:
    have = {t.code: t for t in await session.scalars(select(ScenarioTemplate))}
    for spec in SCENARIO_TEMPLATES:
        row = have.get(spec["code"])
        if row is None:
            session.add(ScenarioTemplate(**spec))
        else:
            for k, v in spec.items():
                setattr(row, k, v)


async def seed() -> None:
    async with session_manager() as session:
        await _seed_room_types(session)
        types = await _seed_device_types(session)
        await _seed_templates(session)
        await _upsert_user(session, settings.DEMO_PHONE, settings.DEMO_PASSWORD, "Тестовый житель", "orion")
        await _upsert_user(session, settings.CONCIERGE_PHONE, settings.CONCIERGE_PASSWORD, "Консьерж", "orion",
                           role="concierge")
        if settings.UJIN_RESIDENT_PHONE and settings.UJIN_RESIDENT_PASSWORD:
            resident = await _upsert_user(session, settings.UJIN_RESIDENT_PHONE, settings.UJIN_RESIDENT_PASSWORD,
                                          "Житель Ujin", "ujin")
            await _seed_ujin_home(session, resident, types)
            await session.flush()
            await _seed_home_scenarios(session, resident)
        else:
            log.warning("UJIN_RESIDENT_PHONE/PASSWORD не заданы в .env — житель Ujin не создан")
        await session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(seed())

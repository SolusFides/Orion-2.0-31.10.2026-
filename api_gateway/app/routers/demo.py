from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import session_manager
from app.dependencies.auth import CurrentUser
from app.models import Device, Home, Scenario, ScenarioTemplate
from app.repositories.device import DeviceRepository
from app.repositories.scenario import ScenarioRepository
from app.schemas.device import SimulateIn
from app.schemas.scenario import FromTemplateIn
from app.services.engine import engine
from app.services.errors import ApiError
from app.services.state import apply_value, state_lock

router = APIRouter(prefix="/api/demo", tags=["Demo"])
devices = DeviceRepository()
RESET = {"leak": {"leak": 0}, "counter": {"load_relay": 1}, "valve": {"valve": 1},
         "fire": {"smoke": 5, "alarm": 0}, "barrier": {"state": 0, "obstacle": 0, "alarm": 0}}


async def _home(user_id: int) -> Home:
    async with session_manager() as session:
        home = await session.scalar(select(Home).where(Home.user_id == user_id).order_by(Home.id.desc()).limit(1))
        if home is None:
            raise ApiError(409, "no_home", "Сначала создайте дом")
        return home


async def _reset(home_id: int) -> None:
    async with state_lock, session_manager() as session:
        rows = await session.scalars(select(Device).where(Device.home_id == home_id)
                                     .options(selectinload(Device.device_type)))
        for d in rows:
            d.online = True
            for signal, value in RESET.get(d.device_type.family or "", {}).items():
                if d.state.get(signal) != value:
                    apply_value(session, d, signal, value, "simulate")
        scenario_ids = list(await session.scalars(select(Scenario.id).where(Scenario.home_id == home_id)))
        await session.commit()
    for sid in scenario_ids:
        engine.last_fire.pop(sid, None)
        await engine.prime(sid)


async def _leak_scenario(user_id: int, home_id: int) -> dict[str, Any]:
    async with session_manager() as session:
        tpl = await session.scalar(select(ScenarioTemplate).where(ScenarioTemplate.code == "leak_protection"))
        s = await session.scalar(select(Scenario).where(Scenario.home_id == home_id, Scenario.template_id == tpl.id,
                                                        Scenario.enabled.is_(True)).order_by(Scenario.id).limit(1))
    if s is None:
        out = await ScenarioRepository().create_from_template(
            user_id, FromTemplateIn(home_id=home_id, template_id=tpl.id, add_virtual_missing=True))
        s_id, conditions, actions = out.scenario.id, out.scenario.conditions, out.scenario.actions
    else:
        s_id, conditions, actions = s.id, s.conditions, s.actions
    valve = next(a["device_id"] for a in actions if a.get("type") == "command")
    return {"scenario_id": s_id, "sensor_id": conditions[0]["device_id"], "valve_id": valve}


@router.post("/leak")
async def demo_leak(user: CurrentUser) -> dict[str, Any]:
    home = await _home(user.id)
    await _reset(home.id)
    ids = await _leak_scenario(user.id, home.id)
    r = await devices.simulate(ids["sensor_id"], user.id, SimulateIn(signal="leak", value=1))
    return {**ids, "triggered_runs": r.triggered_runs}


@router.post("/leak-offline")
async def demo_leak_offline(user: CurrentUser) -> dict[str, Any]:
    home = await _home(user.id)
    await _reset(home.id)
    ids = await _leak_scenario(user.id, home.id)
    await devices.set_online(ids["valve_id"], user.id, False)
    r = await devices.simulate(ids["sensor_id"], user.id, SimulateIn(signal="leak", value=1))
    return {**ids, "triggered_runs": r.triggered_runs}


@router.post("/reset")
async def demo_reset(user: CurrentUser) -> dict[str, Any]:
    home = await _home(user.id)
    await _reset(home.id)
    return {"home_id": home.id, "status": "ok"}



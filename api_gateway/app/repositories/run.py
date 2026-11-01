from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import iso, session_manager
from app.models import Device, Event, Home, Run, Scenario
from app.repositories.home import _load_home
from app.schemas import run as schemas
from app.services import devices as dev
from app.services.errors import ApiError, not_found
from app.services.homes import MODE_TITLES, _value_text


def _brief(r: Run) -> schemas.RunBrief:
    return schemas.RunBrief(id=r.id, scenario=schemas.ScenarioRef(id=r.scenario.id, title=r.scenario.title),
                            status=r.status, dry_run=r.dry_run, reason=r.reason, started_at=iso(r.started_at),
                            finished_at=iso(r.finished_at))


async def _trigger(session: AsyncSession, event_id: int | None) -> schemas.RunTrigger | None:
    if event_id is None:
        return None
    ev = await session.get(Event, event_id)
    if ev is None:
        return None
    if ev.kind == "mode":
        return schemas.RunTrigger(device=None, what=f"Режим дома: {MODE_TITLES.get(ev.value, ev.value)}",
                                  at=iso(ev.at))
    device = await session.scalar(select(Device).where(Device.id == ev.device_id)
                                  .options(selectinload(Device.device_type)))
    what = ev.name
    if device is not None:
        sig = dev.find_signal(device.device_type, ev.name)
        if sig is not None:
            what = f"{sig['title']}: {_value_text(sig, ev.value) or ev.value}"
    return schemas.RunTrigger(device=device.title if device else None, what=what, at=iso(ev.at))


class RunRepository:
    async def list_for_home(self, home_id: int, user_id: int, limit: int, dry: bool) -> list[schemas.RunBrief]:
        async with session_manager() as session:
            await _load_home(session, home_id, user_id)
            q = (select(Run).join(Scenario).where(Scenario.home_id == home_id)
                 .options(selectinload(Run.scenario)).order_by(Run.id.desc()).limit(limit))
            if not dry:
                q = q.where(Run.dry_run.is_(False))
            return [_brief(r) for r in await session.scalars(q)]

    async def list_for_scenario(self, scenario_id: int, user_id: int, limit: int) -> list[schemas.RunBrief]:
        async with session_manager() as session:
            s = await session.get(Scenario, scenario_id)
            if s is None:
                raise not_found("Сценарий", scenario_id)
            try:
                await _load_home(session, s.home_id, user_id)
            except ApiError:
                raise not_found("Сценарий", scenario_id) from None
            rows = await session.scalars(select(Run).where(Run.scenario_id == scenario_id)
                                         .options(selectinload(Run.scenario)).order_by(Run.id.desc()).limit(limit))
            return [_brief(r) for r in rows]

    async def get(self, run_id: int, user_id: int) -> schemas.RunOut:
        async with session_manager() as session:
            r = await session.scalar(select(Run).where(Run.id == run_id)
                                     .options(selectinload(Run.scenario), selectinload(Run.steps)))
            if r is None:
                raise not_found("Запуск", run_id)
            home = await session.get(Home, r.scenario.home_id)
            if home is None or home.user_id != user_id:
                raise not_found("Запуск", run_id)
            return schemas.RunOut(
                **_brief(r).model_dump(),
                trigger=await _trigger(session, r.trigger_event_id),
                steps=[schemas.RunStepOut(idx=st.idx, type=st.type, title=st.title, status=st.status,
                                          attempts=st.attempts, error=st.error, at=iso(st.at))
                       for st in sorted(r.steps, key=lambda st: st.idx)],
            )

    async def scenario_home(self, scenario_id: int, user_id: int) -> Scenario:
        async with session_manager() as session:
            s = await session.get(Scenario, scenario_id)
            if s is None:
                raise not_found("Сценарий", scenario_id)
            try:
                await _load_home(session, s.home_id, user_id)
            except ApiError:
                raise not_found("Сценарий", scenario_id) from None
            return s

import asyncio
import contextvars
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import iso, session_manager, utcnow
from app.models import Device, DeviceCommand, Home, Notification, Run, RunStep, Scenario
from app.services import devices as dev
from app.services.homes import _value_text
from app.services.sse import CONCIERGE, home_channel, hub
from app.services.state import apply_with_physics, compare, state_lock
from app.services.validation import DEFAULT_ON_ERROR

log = logging.getLogger("engine")

TICK_S = 30
MAX_CASCADE = 3
_depth: contextvars.ContextVar[int] = contextvars.ContextVar("cascade_depth", default=0)

@dataclass
class Change:
    home_id: int
    kind: str = "state"
    device_id: int | None = None
    events: list[str] = field(default_factory=list)
    event_id: int | None = None
    fired: set[tuple[int, str]] = field(default_factory=set)


@dataclass
class Ctx:
    home: Home
    devices: dict[int, Device]
    now_hhmm: str
    fired: set[tuple[int, str]]


def _now_hhmm() -> str:
    return datetime.now(ZoneInfo(settings.TIMEZONE)).strftime("%H:%M")


def condition_true(c: dict[str, Any], ctx: Ctx) -> bool:
    t = c.get("type")
    if t == "state":
        d = ctx.devices.get(c.get("device_id"))
        return d is not None and compare(d.state.get(c.get("signal")), c.get("op", "=="), c.get("value"))
    if t == "event":
        return (c.get("device_id"), c.get("event")) in ctx.fired
    if t == "mode":
        return compare(ctx.home.mode, c.get("op", "=="), c.get("value"))
    if t == "time":
        return compare(ctx.now_hhmm, c.get("op", ">="), c.get("value"))
    return False


def scenario_true(s: Scenario, ctx: Ctx) -> bool:
    if not s.conditions:
        return False
    results = [condition_true(c, ctx) for c in s.conditions]
    return any(results) if s.logic == "or" else all(results)


async def _load_home(session: AsyncSession, home_id: int) -> Home | None:
    return await session.scalar(
        select(Home).where(Home.id == home_id).options(
            selectinload(Home.rooms),
            selectinload(Home.devices).selectinload(Device.device_type),
            selectinload(Home.scenarios),
        )
    )


def _ctx(home: Home, fired: set[tuple[int, str]] | None = None) -> Ctx:
    return Ctx(home=home, devices={d.id: d for d in home.devices}, now_hhmm=_now_hhmm(), fired=fired or set())


def _room_title(s: Scenario, home: Home) -> str:
    devices = {d.id: d for d in home.devices}
    rooms = {r.id: r.title for r in home.rooms}
    for part in [*s.conditions, *s.actions]:
        d = devices.get(part.get("device_id"))
        if d is not None and d.room_id in rooms:
            return rooms[d.room_id]
    return ""


def _fmt(text: str, home: Home, room: str) -> str:
    return text.replace("{home}", home.title).replace("{room}", room or "дом")


class Engine:
    def __init__(self) -> None:
        self.last_truth: dict[int, bool] = {}
        self.last_fire: dict[int, datetime] = {}
        self.locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.tasks: set[asyncio.Task] = set()
        self._ticker: asyncio.Task | None = None


    async def start(self) -> None:
        await self.prime_all()
        self._ticker = asyncio.create_task(self._tick_loop())
        log.info("движок запущен: %d сценариев", len(self.last_truth))

    async def stop(self) -> None:
        for t in [self._ticker, *self.tasks]:
            if t is not None:
                t.cancel()

    async def prime_all(self) -> None:
        async with session_manager() as session:
            homes = await session.scalars(select(Home.id))
            for home_id in list(homes):
                home = await _load_home(session, home_id)
                ctx = _ctx(home)
                for s in home.scenarios:
                    self.last_truth[s.id] = scenario_true(s, ctx)
            rows = await session.execute(
                select(Run.scenario_id, func.max(Run.started_at)).where(Run.dry_run.is_(False),
                                                                         Run.status != "skipped")
                .group_by(Run.scenario_id)
            )
            self.last_fire.update({sid: at for sid, at in rows.all()})

    def forget(self, scenario_id: int) -> None:
        self.last_truth.pop(scenario_id, None)

    async def prime(self, scenario_id: int) -> None:
        async with session_manager() as session:
            s = await session.get(Scenario, scenario_id)
            if s is None:
                self.last_truth.pop(scenario_id, None)
                return
            home = await _load_home(session, s.home_id)
            self.last_truth[s.id] = scenario_true(s, _ctx(home))

    async def _tick_loop(self) -> None:
        while True:
            await asyncio.sleep(TICK_S)
            try:
                async with session_manager() as session:
                    rows = await session.scalars(select(Scenario).where(Scenario.enabled.is_(True)))
                    homes = {s.home_id for s in rows if any(c.get("type") == "time" for c in s.conditions)}
                for home_id in homes:
                    await self.on_change(Change(home_id=home_id, kind="time"))
            except Exception:
                log.exception("ошибка тика")


    async def on_change(self, change: Change) -> list[int]:
        if _depth.get() > MAX_CASCADE:
            log.warning("каскад сценариев глубже %d — пропущен", MAX_CASCADE)
            return []
        started: list[int] = []
        async with self.locks[change.home_id]:
            async with session_manager() as session:
                home = await _load_home(session, change.home_id)
                if home is None:
                    return []
                fired = set(change.fired) | ({(change.device_id, e) for e in change.events}
                                             if change.device_id else set())
                ctx = _ctx(home, fired)
                now = utcnow()
                for s in sorted(home.scenarios, key=lambda s: s.id):
                    truth = scenario_true(s, ctx)
                    prev = self.last_truth.get(s.id)
                    self.last_truth[s.id] = truth
                    if prev is None:
                        continue
                    if not (s.enabled and truth and not prev):
                        continue
                    last = self.last_fire.get(s.id)
                    if s.cooldown_s and last and now - last < timedelta(seconds=s.cooldown_s):
                        run = Run(scenario_id=s.id, trigger_event_id=change.event_id, status="skipped",
                                  reason=f"пауза между срабатываниями ({s.cooldown_s} с)", finished_at=now)
                        session.add(run)
                        await session.flush()
                        started.append(run.id)
                        continue
                    run = Run(scenario_id=s.id, trigger_event_id=change.event_id, status="running")
                    session.add(run)
                    await session.flush()
                    self.last_fire[s.id] = now
                    started.append(run.id)
                await session.commit()
        for run_id in started:
            self._spawn(run_id)
        return started

    def _spawn(self, run_id: int) -> None:
        depth = _depth.get()

        async def runner() -> None:
            _depth.set(depth + 1)
            await self.execute(run_id)

        task = asyncio.create_task(runner())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)


    async def run_now(self, scenario_id: int, dry_run: bool = False) -> int:
        async with session_manager() as session:
            run = Run(scenario_id=scenario_id, status="running", dry_run=dry_run,
                      reason="песочница" if dry_run else "запуск вручную")
            session.add(run)
            await session.commit()
            run_id = run.id
        if dry_run:
            await self.execute(run_id)
        else:
            self.last_fire[scenario_id] = utcnow()
            self._spawn(run_id)
        return run_id


    async def execute(self, run_id: int) -> None:
        try:
            await self._execute(run_id)
        except Exception as exc:
            log.exception("запуск %s упал", run_id)
            async with session_manager() as session:
                run = await session.get(Run, run_id)
                if run is not None and run.status == "running":
                    run.status, run.reason, run.finished_at = "failed", f"ошибка движка: {exc}", utcnow()
                    await session.commit()

    async def _execute(self, run_id: int) -> None:
        async with session_manager() as session:
            run = await session.get(Run, run_id)
            if run is None or run.status != "running":
                return
            s = await session.get(Scenario, run.scenario_id)
            home = await _load_home(session, s.home_id)
            dry = run.dry_run
            room = _room_title(s, home)
            on_error = {**DEFAULT_ON_ERROR, **(s.on_error or {})}
            channel = home_channel(home.id)
            hub.publish(channel, "run_started", {"run_id": run.id, "scenario_id": s.id, "title": s.title,
                                                 "dry_run": dry, "at": iso(run.started_at)})

            failed = False
            idx = 0
            for a in s.actions:
                if failed:
                    await self._step(session, run, home.id, idx, a.get("type", "?"), self._title(a, home, room),
                                     "skipped", 0, "пропущено: предыдущий шаг не выполнен")
                    idx += 1
                    continue
                kind = a.get("type")
                if kind == "command":
                    ok = await self._command(session, run, idx, a, home, on_error, dry)
                    failed = not ok
                elif kind == "notify":
                    await self._notify(session, run, idx, a, home, room, s, dry, "notify")
                elif kind == "delay":
                    if not dry:
                        await asyncio.sleep(int(a.get("seconds", 0)))
                    await self._step(session, run, home.id, idx, "delay", self._title(a, home, room), "ok", 1, None)
                idx += 1

            if failed:
                for fb in on_error.get("fallback") or []:
                    await self._notify(session, run, idx, fb, home, room, s, dry, "fallback")
                    idx += 1
                run.status = "fallback" if on_error.get("fallback") else "failed"
            else:
                run.status = "ok"
            run.finished_at = utcnow()
            await session.commit()
            hub.publish(channel, "run_finished", {"run_id": run.id, "scenario_id": s.id, "status": run.status,
                                                  "dry_run": dry, "at": iso(run.finished_at)})
            log.info("запуск %s «%s»: %s%s", run.id, s.title, run.status, " (песочница)" if dry else "")

    def _title(self, a: dict[str, Any], home: Home, room: str) -> str:
        kind = a.get("type")
        if kind == "command":
            d = next((x for x in home.devices if x.id == a.get("device_id")), None)
            if d is None:
                return f"Устройство {a.get('device_id')}: {a.get('signal')} → {a.get('value')}"
            sig = dev.find_signal(d.device_type, a.get("signal")) or {"title": a.get("signal")}
            return f"{d.title}: {sig['title']} → {_value_text(sig, a.get('value')) or a.get('value')}"
        if kind == "notify":
            who = "Консьержу" if a.get("audience") == "concierge" else "Жителю"
            return f"{who}: {_fmt(a.get('text', ''), home, room)}"
        if kind == "delay":
            return f"Пауза {a.get('seconds')} с"
        return str(kind)

    async def _step(self, session: AsyncSession, run: Run, home_id: int, idx: int, kind: str, title: str,
                    status: str, attempts: int, error: str | None) -> RunStep:
        step = RunStep(run_id=run.id, idx=idx, type=kind, title=title[:200], status=status, attempts=attempts,
                       error=error)
        session.add(step)
        await session.commit()
        hub.publish(home_channel(home_id), "run_step", {
            "run_id": run.id, "idx": idx, "type": kind, "title": title, "status": status,
            "attempts": attempts, "error": error,
        })
        return step

    async def _command(self, session: AsyncSession, run: Run, idx: int, a: dict[str, Any], home: Home,
                       on_error: dict[str, Any], dry: bool) -> bool:
        title = self._title(a, home, "")
        attempts_max = int(on_error.get("retries", 3)) + 1
        delay = float(on_error.get("retry_delay_s", 2))
        device = await session.scalar(select(Device).where(Device.id == a.get("device_id"))
                                      .options(selectinload(Device.device_type)))
        error = None
        attempts = 0
        for attempt in range(1, attempts_max + 1):
            attempts = attempt
            if device is None:
                error = "not_found"
                break
            await session.refresh(device, ["online", "state"])
            if device.online:
                error = None
                break
            error = "device_offline"
            if attempt < attempts_max and not dry:
                await asyncio.sleep(delay)
        sig = dev.find_signal(device.device_type, a.get("signal")) if device is not None else None
        if error is None and sig is None:
            error = "unknown_signal"
        ok = error is None
        step = await self._step(session, run, home.id, idx, "command", title, "ok" if ok else "failed", attempts,
                                error)
        if dry or device is None:
            return ok
        cmd = DeviceCommand(device_id=device.id, run_step_id=step.id, signal=a.get("signal"), value=a.get("value"),
                            source="scenario", status="ok" if ok else "failed", error=error, finished_at=utcnow())
        session.add(cmd)
        fired: list[str] = []
        ev_id = None
        async with state_lock:
            if ok:
                await session.refresh(device, ["state"])
                ev, fired = apply_with_physics(session, device, a.get("signal"), a.get("value"), "command",
                                               write_state=sig.get("management") == "rw")
                await session.flush()
                ev_id = ev.id if ev else None
            await session.commit()
        if ok and (ev_id is not None or fired):
            await self.on_change(Change(home_id=device.home_id, device_id=device.id, events=fired, event_id=ev_id))
        return ok

    async def _notify(self, session: AsyncSession, run: Run, idx: int, a: dict[str, Any], home: Home, room: str,
                      s: Scenario, dry: bool, kind: str) -> None:
        text = _fmt(a.get("text", ""), home, room)
        audience = a.get("audience", "resident")
        level = a.get("level", "info")
        title = self._title(a, home, room)
        if kind == "fallback":
            title = "План Б — " + title
        if not dry:
            n = Notification(home_id=home.id, run_id=run.id, audience=audience, level=level, title=s.title, text=text)
            session.add(n)
            await session.flush()
            payload = {"id": n.id, "home_id": home.id, "home": home.title, "audience": audience, "level": level,
                       "title": s.title, "text": text, "run_id": run.id, "at": iso(n.created_at)}
            hub.publish(CONCIERGE if audience == "concierge" else home_channel(home.id), "notification", payload)
        await self._step(session, run, home.id, idx, kind, title, "ok", 1, "песочница: не отправлено" if dry else None)


engine = Engine()

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import session_manager
from app.models import Device
from app.services import physics
from app.services.engine import Change, engine
from app.services.state import apply_value, state_lock

log = logging.getLogger("emulator")


class Emulator:
    def __init__(self) -> None:
        self.ticks = 0
        self.devices = 0
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())
        log.info("эмуляторы запущены: тик %s с", settings.EMULATOR_TICK_S)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(settings.EMULATOR_TICK_S)
            try:
                await self.tick(settings.EMULATOR_TICK_S)
            except Exception:
                log.exception("ошибка тика эмулятора")

    async def tick(self, dt: float) -> int:
        self.ticks += 1
        now = time.time()
        changes: dict[int, Change] = {}
        async with state_lock, session_manager() as session:
            devices = list(await session.scalars(
                select(Device).where(Device.online.is_(True)).options(selectinload(Device.device_type))))
            self.devices = len(devices)
            for d in devices:
                updates = physics.tick(d.device_type.family, d.id, d.state, dt, self.ticks, now)
                if not updates:
                    continue
                fired: list[str] = []
                event_id: Any = None
                for signal, value in updates.items():
                    ev, f = apply_value(session, d, signal, value, "emulator",
                                        history=signal not in physics.CONTINUOUS)
                    fired += f
                    if ev is not None:
                        await session.flush()
                        event_id = ev.id
                ch = changes.setdefault(d.home_id, Change(home_id=d.home_id))
                ch.fired |= {(d.id, e) for e in fired}
                ch.event_id = event_id or ch.event_id
                ch.device_id = d.id
            await session.commit()
        for ch in changes.values():
            await engine.on_change(ch)
        return len(changes)

    def status(self) -> dict[str, Any]:
        return {"running": self._task is not None and not self._task.done(), "tick_s": settings.EMULATOR_TICK_S,
                "ticks": self.ticks, "devices_online": self.devices}


emulator = Emulator()

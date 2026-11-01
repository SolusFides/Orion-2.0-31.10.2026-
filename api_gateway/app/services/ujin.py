import asyncio
import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import iso, session_manager, utcnow
from app.models import Device, UjinSyncLog
from app.services import devices as dev

log = logging.getLogger("ujin")
METHOD = "import_device/group-update-device-signal"


def wire(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1 if value else 0.001
    if isinstance(value, (int, float)):
        return 0.001 if value == 0 else value
    return None


class UjinPublisher:
    def __init__(self) -> None:
        self.dirty: dict[int, set[str]] = {}
        self.dicts_created: set[int] = set()
        self.last_publish_at = None
        self.last_error: str | None = None
        self.published = 0
        self._task: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        return settings.UJIN_PUBLISH_ENABLED and bool(settings.UJIN_UST)

    def mark(self, device_id: int, signal: str) -> None:
        if self.enabled:
            self.dirty.setdefault(device_id, set()).add(signal)

    async def start(self) -> None:
        if self.enabled:
            self._task = asyncio.create_task(self._loop())
            log.info("публикация в Ujin включена: раз в %s с", settings.UJIN_PUBLISH_INTERVAL_S)
        else:
            log.info("публикация в Ujin выключена (UJIN_PUBLISH_ENABLED / UJIN_UST)")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(settings.UJIN_PUBLISH_INTERVAL_S)
            try:
                await self.flush()
            except Exception as exc:
                self.last_error = str(exc)
                log.exception("ошибка публикации")

    async def flush(self, full: bool = False) -> list[dict[str, Any]]:
        pending, self.dirty = self.dirty, {}
        results = []
        async with session_manager() as session:
            q = select(Device).where(Device.mode == "ujin", Device.ujin_ext_guid.is_not(None)) \
                .options(selectinload(Device.device_type))
            for d in await session.scalars(q):
                names = [s["name"] for s in dev.signals(d.device_type) if dev.readable(s)] if full \
                    else sorted(pending.get(d.id, ()))
                if names:
                    results.append(await self._publish(session, d, names))
            await session.commit()
        return results

    async def _publish(self, session, d: Device, names: list[str]) -> dict[str, Any]:
        cls = settings.UJIN_PUBLISH_CLASS
        values = {n: wire(d.state.get(n)) for n in names}
        values = {n: v for n, v in values.items() if v is not None}
        if not values:
            return {"device_id": d.id, "status": "skip"}
        if d.id not in self.dicts_created:
            first = [{"sn": d.ujin_ext_guid, "s": n, "v": 0.001, "c": cls}
                     for n in (s["name"] for s in dev.signals(d.device_type) if dev.readable(s))]
            ok, error = await self._post(session, d, first, "dicts")
            if not ok:
                return {"device_id": d.id, "status": "error", "signals": [], "error": error}
            self.dicts_created.add(d.id)
            await asyncio.sleep(2)
        rows = [{"sn": d.ujin_ext_guid, "s": f"{cls}_{n}", "v": v, "c": cls} for n, v in values.items()]
        ok, error = await self._post(session, d, rows, "values")
        return {"device_id": d.id, "status": "ok" if ok else "error", "signals": list(values), "error": error}

    async def _post(self, session, d: Device, rows: list[dict[str, Any]], phase: str) -> tuple[bool, str | None]:
        params = {"token": settings.UJIN_UST, "apartment_id": settings.UJIN_APARTMENT_ID,
                  "serialnumber": d.ujin_ext_guid}
        url = f"{settings.UJIN_API_BASE.rstrip('/')}/{METHOD}/"
        error = None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, params=params, json={"data": rows})
            body = r.json()
            result = (body.get("data") or {}).get("result") if isinstance(body.get("data"), dict) else None
            if r.status_code != 200 or body.get("error") not in (0, "0"):
                error = f"HTTP {r.status_code}: {str(body.get('message') or body)[:200]}"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:300]
            result = None
        session.add(UjinSyncLog(direction="up", device_id=d.id, method=f"{METHOD} ({phase})",
                                payload={"data": rows, "stand_result": result},
                                status="error" if error else "ok", error=error))
        if error:
            self.last_error = error
            log.warning("Ujin %s %s: %s", d.ujin_ext_guid, phase, error)
        else:
            self.last_publish_at = utcnow()
            self.last_error = None
            self.published += len(rows)
        return error is None, error

    def status(self) -> dict[str, Any]:
        return {
            "stand": "uae-test", "enabled": self.enabled,
            "connected": self.enabled and self.last_error is None,
            "last_publish_at": iso(self.last_publish_at),
            "published_values": self.published,
            "features": {"publish_values": True, "commands_down": False, "autoscripts_trigger": False},
        }


publisher = UjinPublisher()

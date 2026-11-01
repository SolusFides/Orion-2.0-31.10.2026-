from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.database import iso, session_manager
from app.models import Event, Notification, Run, Scenario
from app.repositories.home import _load_home
from app.schemas.journal import JournalItem
from app.services import devices as dev
from app.services.homes import MODE_TITLES

RUN_TEXT = {"ok": "выполнено", "fallback": "не вышло — план Б", "failed": "не выполнено",
            "skipped": "пропущено", "running": "выполняется"}
RUN_LEVEL = {"ok": "ok", "fallback": "warning", "failed": "alarm", "skipped": "info", "running": "info"}


def event_level(device, event_name):
    e = dev.find_event(device.device_type, event_name)
    if e is None:
        return "info"
    sig = dev.find_signal(device.device_type, e["when"].get("signal")) or {}
    if e["when"].get("value") in (sig.get("alarm_values") or []):
        return "alarm"
    return "warning" if e["when"].get("op") in ("<", "<=") else "info"


def event_item(e, home, devices):
    if e.kind == "mode":
        return JournalItem(kind="mode", at=iso(e.at), level="info",
                           title=f"Режим дома: {MODE_TITLES.get(e.value, e.value)}",
                           text="вы" if e.source == "user" else e.source)
    d = devices.get(e.device_id)
    if d is None:
        return None
    if e.kind == "state":
        return JournalItem(kind="online", at=iso(e.at), device_id=d.id, level="info" if e.value else "warning",
                           title=f"{d.title}: {'связь есть' if e.value else 'нет связи'}")
    ev = dev.find_event(d.device_type, e.name) or {"title": e.name}
    room = next((r.title for r in home.rooms if r.id == d.room_id), None)
    return JournalItem(kind="event", at=iso(e.at), device_id=d.id, level=event_level(d, e.name),
                       title=f"{d.title}: {ev['title']}", text=room)


def run_item(r):
    failed = next((s for s in sorted(r.steps, key=lambda s: s.idx) if s.status == "failed"), None)
    done = sum(1 for s in r.steps if s.status == "ok")
    text = r.reason or (f"{failed.title} — {failed.error}" if failed else f"шагов: {done}")
    return JournalItem(kind="run", at=iso(r.started_at), run_id=r.id, status=r.status,
                       level=RUN_LEVEL.get(r.status, "info"),
                       title=f"{r.scenario.title} — {RUN_TEXT.get(r.status, r.status)}", text=text)


def notification_item(n):
    if n.audience == "concierge":
        title = "Консьержу отправлена " + ("тревога" if n.level == "alarm" else "заявка")
        if n.status == "acked":
            title += " — принято"
    else:
        title = f"Вам: {n.title}"
    return JournalItem(kind="notification", at=iso(n.created_at), title=title, text=n.text, level=n.level,
                       run_id=n.run_id, audience=n.audience, status=n.status)


class JournalRepository:
    async def for_home(self, home_id, user_id, limit):
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            devices = {d.id: d for d in home.devices}
            events = await session.scalars(
                select(Event).where(Event.home_id == home_id,
                                    or_(Event.kind.in_(["event", "mode"]),
                                        (Event.kind == "state") & (Event.name == "online")))
                .order_by(Event.id.desc()).limit(limit)
            )
            runs = await session.scalars(
                select(Run).join(Scenario).where(Scenario.home_id == home_id, Run.dry_run.is_(False))
                .options(selectinload(Run.scenario), selectinload(Run.steps))
                .order_by(Run.id.desc()).limit(limit)
            )
            notes = await session.scalars(
                select(Notification).where(Notification.home_id == home_id)
                .order_by(Notification.id.desc()).limit(limit)
            )
            items = [(e.at, event_item(e, home, devices)) for e in events]
            items += [(r.started_at, run_item(r)) for r in runs]
            items += [(n.created_at, notification_item(n)) for n in notes]
            items = [x for x in items if x[1] is not None]
            items.sort(key=lambda x: x[0], reverse=True)
            return [i for _, i in items[:limit]]

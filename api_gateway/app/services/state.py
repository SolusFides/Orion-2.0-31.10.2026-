import asyncio
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import iso, utcnow
from app.models import Device, Event
from app.services import devices as dev
from app.services.homes import _value_text
from app.services import physics
from app.services.sse import home_channel, hub
from app.services.ujin import publisher

state_lock = asyncio.Lock()

OPS = {
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
}


def compare(left: Any, op: str, right: Any) -> bool:
    try:
        return left is not None and OPS[op](left, right)
    except (TypeError, KeyError):
        return False


def holds(when: dict[str, Any], state: dict[str, Any]) -> bool:
    return compare(state.get(when.get("signal")), when.get("op", "=="), when.get("value"))


def apply_value(session: AsyncSession, device: Device, signal: str, value: Any, source: str,
                history: bool = True) -> tuple[Event | None, list[str]]:
    prev_state = dict(device.state)
    device.state = {**device.state, signal: value}
    device.last_seen_at = utcnow()
    ev = None
    if history:
        ev = Event(home_id=device.home_id, device_id=device.id, kind="state", name=signal, value=value,
                   prev_value=prev_state.get(signal), source=source)
        session.add(ev)
    fired: list[str] = []
    for e in (device.device_type.declaration or {}).get("events", []):
        when = e.get("when", {})
        if when.get("signal") == signal and holds(when, device.state) and not holds(when, prev_state):
            ev_fired = Event(home_id=device.home_id, device_id=device.id, kind="event", name=e["name"], value=value,
                             source=source)
            session.add(ev_fired)
            ev = ev or ev_fired
            fired.append(e["name"])
    if device.mode == "ujin" and device.ujin_ext_guid:
        publisher.mark(device.id, signal)
    sig = dev.find_signal(device.device_type, signal) or {}
    hub.publish(home_channel(device.home_id), "device_state", {
        "device_id": device.id, "signal": signal, "value": value, "text": _value_text(sig, value),
        "source": source, "at": iso(device.last_seen_at),
    })
    return ev, fired


def apply_with_physics(session: AsyncSession, device: Device, signal: str, value: Any, source: str,
                       write_state: bool = True) -> tuple[Event | None, list[str]]:
    ev, fired = (apply_value(session, device, signal, value, source) if write_state else (None, []))
    reactions = physics.react(device.device_type.family, device.id, device.state, signal, value, time.time())
    for s, v in reactions.items():
        ev2, f2 = apply_value(session, device, s, v, "emulator", history=s not in physics.CONTINUOUS)
        ev = ev or ev2
        fired += f2
    return ev, fired

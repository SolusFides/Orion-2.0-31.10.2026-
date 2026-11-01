from typing import Any

from app.models import Device, Home, Room, Scenario
from app.schemas import home as schemas

LOW_BATTERY = 20
MODE_TITLES = {"home": "Дома", "away": "Ушёл", "night": "Ночь"}


def scenario_device_ids(s: Scenario) -> set[int]:
    ids: set[int] = set()
    for part in [*s.conditions, *s.actions]:
        if isinstance(part, dict) and isinstance(part.get("device_id"), int):
            ids.add(part["device_id"])
    return ids


def _value_text(signal: dict[str, Any], value: Any) -> str | None:
    for v in signal.get("values") or []:
        if v.get("value") == value:
            return v.get("text")
    unit = signal.get("unit")
    if value is None:
        return None
    return f"{value} {unit}" if unit else str(value)


def device_summary(d: Device) -> schemas.DeviceSummary | None:
    signals = (d.device_type.declaration or {}).get("signals", [])
    props = [s for s in signals if s.get("group") == "property"]
    sig = next((s for s in signals if s.get("summary")), None) or (props[0] if props else None)
    if sig is None:
        return None
    value = d.state.get(sig["name"])
    level = "alarm" if value in (sig.get("alarm_values") or []) else "ok"
    return schemas.DeviceSummary(signal=sig["name"], value=value, text=_value_text(sig, value), level=level)


def device_brief(d: Device) -> schemas.DeviceBrief:
    return schemas.DeviceBrief(
        id=d.id, title=d.title, type=d.device_type.code, icon=d.device_type.icon,
        mode=d.mode, online=d.online, summary=device_summary(d),
    )


def scenario_briefs(scenarios: list[Scenario], last: dict[int, str]) -> list[schemas.ScenarioBrief]:
    return [
        schemas.ScenarioBrief(id=s.id, title=s.title, description=s.description, enabled=s.enabled, source=s.source, last_run=last.get(s.id))
        for s in scenarios
    ]


def room_out(room: Room, devices: list[Device], scenarios: list[Scenario]) -> schemas.RoomOut:
    dev_ids = {d.id for d in devices}
    return schemas.RoomOut(
        id=room.id, type=room.room_type_code, title=room.title,
        devices=[device_brief(d) for d in devices],
        scenarios_count=sum(1 for s in scenarios if scenario_device_ids(s) & dev_ids),
    )


def home_short(home: Home) -> schemas.HomeShort:
    return schemas.HomeShort(id=home.id, title=home.title, address=home.address, source=home.source, mode=home.mode)


def home_detail(home: Home, last_runs: dict[int, str], unread: int) -> schemas.HomeOut:
    devices = sorted(home.devices, key=lambda d: d.id)
    by_room: dict[int | None, list[Device]] = {}
    for d in devices:
        by_room.setdefault(d.room_id, []).append(d)
    scenarios = sorted(home.scenarios, key=lambda s: s.id)
    low_battery = sum(
        1 for d in devices if isinstance(d.state.get("battery"), (int, float)) and d.state["battery"] < LOW_BATTERY
    )
    return schemas.HomeOut(
        **home_short(home).model_dump(),
        health=schemas.Health(
            devices_total=len(devices), offline=sum(1 for d in devices if not d.online), low_battery=low_battery
        ),
        rooms=[room_out(r, by_room.get(r.id, []), scenarios) for r in home.rooms],
        unassigned_devices=[device_brief(d) for d in by_room.get(None, [])],
        scenarios=scenario_briefs(scenarios, last_runs),
        unread_notifications=unread,
    )


def room_detail(home: Home, room: Room, last_runs: dict[int, str]) -> schemas.RoomDetail:
    devices = sorted((d for d in home.devices if d.room_id == room.id), key=lambda d: d.id)
    dev_ids = {d.id for d in devices}
    scenarios = [s for s in sorted(home.scenarios, key=lambda s: s.id) if scenario_device_ids(s) & dev_ids]
    base = room_out(room, devices, scenarios)
    return schemas.RoomDetail(**base.model_dump(), home_id=home.id, scenarios=scenario_briefs(scenarios, last_runs))

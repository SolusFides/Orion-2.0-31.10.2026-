from typing import Any

from app.database import iso
from app.models import Device, DeviceType, Scenario
from app.schemas import device as schemas
from app.services.homes import _value_text

NUMERIC = {"range", "counter", "graph"}


def signals(dtype: DeviceType) -> list[dict[str, Any]]:
    return (dtype.declaration or {}).get("signals", [])


def find_signal(dtype: DeviceType, name: str) -> dict[str, Any] | None:
    return next((s for s in signals(dtype) if s["name"] == name), None)


def find_event(dtype: DeviceType, name: str) -> dict[str, Any] | None:
    return next((e for e in (dtype.declaration or {}).get("events", []) if e["name"] == name), None)


def writable(sig: dict[str, Any]) -> bool:
    return sig.get("management") in ("rw", "w")


def readable(sig: dict[str, Any]) -> bool:
    return sig.get("management") in ("r", "rw")


def check_value(sig: dict[str, Any], value: Any) -> tuple[str, str] | None:
    if sig.get("control") == "button":
        return None
    if sig.get("values"):
        allowed = [v["value"] for v in sig["values"]]
        if value not in allowed:
            texts = ", ".join(f"{v['value']} — {v['text']}" for v in sig["values"])
            return "value_out_of_range", f"«{sig['title']}»: допустимо {texts}"
        return None
    if sig.get("control") in NUMERIC or "min" in sig or "max" in sig:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "validation_error", f"«{sig['title']}»: нужно число"
        lo, hi = sig.get("min"), sig.get("max")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            return "value_out_of_range", f"«{sig['title']}»: от {lo} до {hi}"
    return None


def signal_value(sig: dict[str, Any], state: dict[str, Any]) -> schemas.SignalValue:
    value = state.get(sig["name"])
    return schemas.SignalValue(
        name=sig["name"], title=sig["title"], control=sig.get("control", "text"),
        management=sig.get("management", "r"), value=value,
        text=_value_text(sig, value), unit=sig.get("unit"), min=sig.get("min"), max=sig.get("max"),
        values=sig.get("values"),
    )


def scenario_refs(device: Device, scenarios: list[Scenario]) -> list[schemas.DeviceScenarioRef]:
    refs = []
    for s in sorted(scenarios, key=lambda s: s.id):
        in_cond = any(c.get("device_id") == device.id for c in s.conditions)
        in_act = any(a.get("device_id") == device.id for a in s.actions)
        if in_cond or in_act:
            refs.append(schemas.DeviceScenarioRef(id=s.id, title=s.title, role="condition" if in_cond else "action"))
    return refs


def device_out(device: Device, scenarios: list[Scenario]) -> schemas.DeviceOut:
    dtype = device.device_type
    groups: dict[str, list[schemas.SignalValue]] = {"property": [], "capability": [], "setting": []}
    for sig in signals(dtype):
        if sig.get("group") in groups:
            groups[sig["group"]].append(signal_value(sig, device.state))
    return schemas.DeviceOut(
        id=device.id, home_id=device.home_id, title=device.title,
        room=schemas.RoomRef(id=device.room.id, title=device.room.title) if device.room else None,
        type=schemas.TypeRef(id=dtype.id, code=dtype.code, title=dtype.title, icon=dtype.icon),
        mode=device.mode, online=device.online, last_seen_at=iso(device.last_seen_at),
        groups=schemas.Groups(**groups),
        events=[schemas.NamedRef(name=e["name"], title=e["title"]) for e in (dtype.declaration or {}).get("events", [])],
        scenarios=scenario_refs(device, scenarios),
        buy_url=dtype.buy_url,
        ujin=schemas.UjinRef(linked=device.mode == "ujin", ext_guid=device.ujin_ext_guid),
    )


def device_type_out(dtype: DeviceType) -> schemas.DeviceTypeOut:
    count = {"property": 0, "capability": 0, "setting": 0}
    for sig in signals(dtype):
        if sig.get("group") in count:
            count[sig["group"]] += 1
    return schemas.DeviceTypeOut(
        id=dtype.id, code=dtype.code, title=dtype.title, family=dtype.family, icon=dtype.icon,
        is_custom=dtype.is_custom, signals_count=schemas.SignalsCount(**count),
        events_count=len((dtype.declaration or {}).get("events", [])), buy_url=dtype.buy_url,
    )

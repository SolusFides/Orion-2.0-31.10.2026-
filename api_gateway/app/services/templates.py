import copy
from typing import Any

from app.models import Device, DeviceType, Home, Room, ScenarioTemplate
from app.schemas import scenario as schemas

WHOLE_HOME: list[str] = []
OUTDOOR = ["outdoor"]

Bindings = dict[str, list[Device]]


def _candidates(home: Home, spec: dict[str, Any], tpl: ScenarioTemplate, room: Room | None) -> list[Device]:
    types = spec["types"]
    devices = [d for d in sorted(home.devices, key=lambda d: d.id) if d.device_type.code in types]
    room_codes = {r.id: r.room_type_code for r in home.rooms}

    def rank(d: Device) -> tuple[int, int, int]:
        in_room = 0 if room is not None and d.room_id == room.id else 1
        fits = 0 if room_codes.get(d.room_id) in tpl.room_types else 1
        return (in_room, fits, types.index(d.device_type.code))

    return sorted(devices, key=rank)


def bind(home: Home, tpl: ScenarioTemplate, room: Room | None = None) -> tuple[Bindings, list[dict[str, Any]]]:
    bindings: Bindings = {}
    missing: list[dict[str, Any]] = []
    optional_missing: list[dict[str, Any]] = []
    for spec in tpl.requires:
        found = _candidates(home, spec, tpl, room)
        if not found:
            (optional_missing if spec.get("optional") else missing).append(spec)
        else:
            bindings[spec["role"]] = found if spec.get("multi") else found[:1]
    if not bindings and not missing and optional_missing:
        missing.append(optional_missing[0])
    return bindings, missing


def visible(home: Home, tpl: ScenarioTemplate) -> bool:
    if tpl.room_types == WHOLE_HOME:
        return True
    if tpl.room_types == OUTDOOR:
        return not bind(home, tpl)[1]
    return bool({r.room_type_code for r in home.rooms} & set(tpl.room_types))


def template_out(home: Home, tpl: ScenarioTemplate, types: dict[str, DeviceType],
                 room: Room | None = None) -> schemas.TemplateOut:
    bindings, missing = bind(home, tpl, room)
    rooms_by_id = {r.id: r for r in home.rooms}
    uses = []
    for spec in tpl.requires:
        for d in bindings.get(spec["role"], []):
            room = rooms_by_id.get(d.room_id)
            uses.append(schemas.TemplateUse(role=spec["role"], title=spec["title"], type=d.device_type.code,
                                            device_id=d.id, device_title=d.title,
                                            room=room.title if room else None))
    return schemas.TemplateOut(
        id=tpl.id, code=tpl.code, title=tpl.title, description=tpl.description, room_types=tpl.room_types,
        rooms=[schemas.RoomRef(id=r.id, title=r.title) for r in home.rooms if r.room_type_code in tpl.room_types],
        ready=not missing,
        uses=uses,
        missing=[schemas.TemplateMissing(role=s["role"], title=s["title"], type=s["types"][0],
                                         buy_url=types[s["types"][0]].buy_url if s["types"][0] in types else None)
                 for s in missing],
    )


def virtual_room(home: Home, tpl: ScenarioTemplate, room: Room | None) -> Room | None:
    if room is not None:
        return room
    return next((r for r in home.rooms if r.room_type_code in tpl.room_types), None)


def _with_device(part: dict[str, Any], bindings: Bindings) -> dict[str, Any]:
    part = copy.deepcopy(part)
    role = part.pop("role", None)
    if role is not None:
        part["device_id"] = bindings[role][0].id
    return part


def build_scenario(tpl: ScenarioTemplate, bindings: Bindings, room: Room | None) -> dict[str, Any]:
    rule = tpl.rule
    actions: list[dict[str, Any]] = []
    for a in rule.get("actions", []):
        if a.get("type") == "command" and "role" in a:
            for d in bindings.get(a["role"], []):
                signal = a["signal"][d.device_type.code] if isinstance(a["signal"], dict) else a["signal"]
                actions.append({"type": "command", "device_id": d.id, "signal": signal, "value": a["value"]})
        else:
            actions.append(copy.deepcopy(a))
    title = tpl.title
    if room is not None and tpl.room_types not in (WHOLE_HOME, OUTDOOR):
        title = f"{tpl.title} · {room.title}"
    return {
        "title": title,
        "description": tpl.description,
        "source": "template",
        "template_id": tpl.id,
        "enabled": True,
        "conditions": [_with_device(c, bindings) for c in rule.get("conditions", [])],
        "logic": rule.get("logic", "and"),
        "actions": actions,
        "on_error": copy.deepcopy(rule.get("on_error", {})),
        "cooldown_s": rule.get("cooldown_s", 60),
    }

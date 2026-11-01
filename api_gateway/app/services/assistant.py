import logging
from typing import Any

from app.models import DeviceType, Home, Room, ScenarioTemplate
from app.services import llm
from app.services import templates as tpl_svc

log = logging.getLogger("assistant")

ROOM_WORDS = {"ванн": "bathroom", "туалет": "toilet", "санузел": "toilet", "кухн": "kitchen",
              "спальн": "bedroom", "гостин": "living", "комнат": "living", "зал": "living",
              "коридор": "hallway", "прихож": "hallway"}


def _norm(s: str) -> str:
    return s.lower().replace("ё", "е")


def find_room(text: str, home: Home) -> Room | None:
    t = _norm(text)
    for r in home.rooms:
        if _norm(r.title) in t:
            return r
    for word, code in ROOM_WORDS.items():
        if word in t:
            return next((r for r in home.rooms if r.room_type_code == code), None)
    return None


def score(text: str, tpl: ScenarioTemplate) -> int:
    t = _norm(text)
    s = sum(1 for k in tpl.keywords if _norm(k) in t)
    if _norm(tpl.title) in t:
        s += 2
    return s


async def propose(text: str, home: Home, templates: list[ScenarioTemplate],
                  types: dict[str, DeviceType]) -> tuple[dict[str, Any] | None, str, list[str]]:
    try:
        draft = await llm.propose(text, {"home": home.title})
        return draft, "Готово, вот предложение.", []
    except llm.LLMUnavailable as exc:
        log.info("LLM недоступна (%s) — подбор по ключевым словам", exc)

    ranked = sorted(((score(text, t), tpl_svc.visible(home, t), -t.id, t) for t in templates),
                    key=lambda x: x[:3], reverse=True)
    examples = [f"«{t.title}»" for _, vis, _, t in ranked if vis][:3]
    best_score, _, _, tpl = ranked[0] if ranked else (0, False, 0, None)
    if not best_score or tpl is None:
        return None, ("Пока я подбираю сценарии из каталога. Попробуйте, например: «при протечке перекрой воду», "
                      "«ночью свет на 30 %», «когда ухожу — выключи свет»."), examples

    room = find_room(text, home)
    out = tpl_svc.template_out(home, tpl, types, room)
    bindings, missing = tpl_svc.bind(home, tpl, room)
    scenario = tpl_svc.build_scenario(tpl, bindings, room) if not missing else None
    explain = [tpl.description] + [f"Использую: {u.device_title}" + (f" ({u.room})" if u.room else "")
                                   for u in out.uses]
    proposal = {
        "template_id": tpl.id, "template_code": tpl.code, "title": tpl.title, "description": tpl.description,
        "room": {"id": room.id, "title": room.title} if room else None,
        "explain": explain, "missing": [m.model_dump() for m in out.missing], "ready": not missing,
        "scenario": scenario, "engine": "keywords",
    }
    if missing:
        names = ", ".join(m.title.lower() for m in out.missing)
        reply = f"Предлагаю «{tpl.title}». Не хватает: {names} — могу добавить виртуальным, чтобы проверить сразу."
    else:
        reply = f"Предлагаю «{tpl.title}». Все устройства у вас есть."
    suggestions = [f"Добавить {e}?" for e in examples if e != f"«{tpl.title}»"][:2]
    return proposal, reply, suggestions

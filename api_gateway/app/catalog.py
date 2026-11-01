ROOM_TYPES = [
    {"code": "bathroom", "title": "Ванная", "icon": "bath"},
    {"code": "toilet", "title": "Туалет", "icon": "wc"},
    {"code": "kitchen", "title": "Кухня", "icon": "kitchen"},
    {"code": "bedroom", "title": "Спальня", "icon": "bed"},
    {"code": "living", "title": "Комната", "icon": "sofa"},
    {"code": "hallway", "title": "Коридор", "icon": "door"},
]


def _onoff(off: str, on: str) -> list[dict]:
    return [{"value": 0, "text": off}, {"value": 1, "text": on}]


DEVICE_TYPES = [
    {
        "code": "leak", "title": "Датчик протечки", "family": "leak", "icon": "drop",
        "declaration": {
            "signals": [
                {"name": "leak", "title": "Протечка", "group": "property", "control": "list", "management": "r",
                 "values": _onoff("Сухо", "Протечка"), "summary": True, "alarm_values": [1]},
                {"name": "battery", "title": "Батарея", "group": "property", "control": "counter",
                 "management": "r", "unit": "%", "min": 0, "max": 100},
                {"name": "tamper", "title": "Вскрытие корпуса", "group": "property", "control": "list",
                 "management": "r", "values": _onoff("Закрыт", "Вскрыт"), "alarm_values": [1]},
                {"name": "self_test", "title": "Самотест", "group": "capability", "control": "button",
                 "management": "w"},
            ],
            "events": [
                {"name": "leak_detected", "title": "Обнаружена протечка",
                 "when": {"signal": "leak", "op": "==", "value": 1}},
                {"name": "battery_low", "title": "Батарея разряжена",
                 "when": {"signal": "battery", "op": "<", "value": 20}},
            ],
        },
        "initial": {"leak": 0, "battery": 87, "tamper": 0},
    },
    {
        "code": "counter", "title": "Счётчик холодной воды", "family": "counter", "icon": "counter",
        "declaration": {
            "signals": [
                {"name": "total", "title": "Показание", "group": "property", "control": "counter",
                 "management": "r", "unit": "м³", "summary": True},
                {"name": "flow", "title": "Расход сейчас", "group": "property", "control": "graph",
                 "management": "r", "unit": "м³/ч"},
                {"name": "battery", "title": "Батарея", "group": "property", "control": "graph",
                 "management": "r", "unit": "%", "min": 0, "max": 100},
                {"name": "load_relay", "title": "Кран", "group": "capability", "control": "switch",
                 "management": "rw", "values": _onoff("Перекрыт", "Открыт")},
                {"name": "report_period", "title": "Период отчёта", "group": "setting", "control": "counter",
                 "management": "rw", "unit": "с", "min": 10, "max": 3600},
            ],
            "events": [
                {"name": "water_closed", "title": "Вода перекрыта",
                 "when": {"signal": "load_relay", "op": "==", "value": 0}},
            ],
        },
        "initial": {"total": 1024.3, "flow": 0.0, "battery": 98, "load_relay": 1, "report_period": 60},
    },
    {
        "code": "thermostat", "title": "Термостат", "family": "thermostat", "icon": "thermo",
        "declaration": {
            "signals": [
                {"name": "temperature", "title": "Температура", "group": "property", "control": "graph",
                 "management": "r", "unit": "°C", "summary": True},
                {"name": "humidity", "title": "Влажность", "group": "property", "control": "graph",
                 "management": "r", "unit": "%"},
                {"name": "output", "title": "Работает", "group": "property", "control": "list", "management": "r",
                 "values": [{"value": 0, "text": "Нет"}, {"value": 1, "text": "Нагрев"},
                            {"value": 2, "text": "Охлаждение"}]},
                {"name": "fault", "title": "Авария датчика", "group": "property", "control": "list",
                 "management": "r", "values": _onoff("Нет", "Нет данных"), "alarm_values": [1]},
                {"name": "mode", "title": "Режим", "group": "capability", "control": "list", "management": "rw",
                 "values": [{"value": 0, "text": "Выкл"}, {"value": 1, "text": "Нагрев"},
                            {"value": 2, "text": "Охлаждение"}, {"value": 3, "text": "Авто"}]},
                {"name": "target_temp", "title": "Цель", "group": "setting", "control": "range",
                 "management": "rw", "unit": "°C", "min": 5, "max": 35},
            ],
            "events": [
                {"name": "sensor_fault", "title": "Авария датчика",
                 "when": {"signal": "fault", "op": "==", "value": 1}},
            ],
        },
        "initial": {"temperature": 21.5, "humidity": 45, "output": 0, "fault": 0, "mode": 3, "target_temp": 22},
    },
    {
        "code": "light", "title": "Светильник", "family": "light", "icon": "bulb",
        "declaration": {
            "signals": [
                {"name": "lamp", "title": "Свет", "group": "capability", "control": "switch", "management": "rw",
                 "values": _onoff("Выкл", "Вкл"), "summary": True},
                {"name": "brightness", "title": "Яркость", "group": "capability", "control": "range",
                 "management": "rw", "unit": "%", "min": 1, "max": 100},
                {"name": "power_w", "title": "Мощность", "group": "property", "control": "graph",
                 "management": "r", "unit": "Вт"},
                {"name": "energy_kwh", "title": "Энергия", "group": "property", "control": "counter",
                 "management": "r", "unit": "кВт·ч"},
                {"name": "offline_timeout", "title": "Авто-выкл через", "group": "setting", "control": "counter",
                 "management": "rw", "unit": "с", "min": 0, "max": 3600},
            ],
            "events": [
                {"name": "turned_on", "title": "Свет включили", "when": {"signal": "lamp", "op": "==", "value": 1}},
            ],
        },
        "initial": {"lamp": 0, "brightness": 100, "power_w": 0.0, "energy_kwh": 0.0, "offline_timeout": 0},
    },
    {
        "code": "barrier", "title": "Шлагбаум", "family": "barrier", "icon": "barrier",
        "declaration": {
            "signals": [
                {"name": "state", "title": "Стрела", "group": "property", "control": "list", "management": "r",
                 "values": [{"value": 0, "text": "Закрыт"}, {"value": 1, "text": "Открывается"},
                            {"value": 2, "text": "Открыт"}, {"value": 3, "text": "Закрывается"},
                            {"value": 4, "text": "Удержание"}], "summary": True},
                {"name": "obstacle", "title": "Предмет под стрелой", "group": "property", "control": "list",
                 "management": "r", "values": _onoff("Нет", "Есть")},
                {"name": "alarm", "title": "Авария", "group": "property", "control": "list", "management": "r",
                 "values": _onoff("Нет", "Застревание"), "alarm_values": [1]},
                {"name": "cycles", "title": "Циклов открытий", "group": "property", "control": "counter",
                 "management": "r"},
                {"name": "open_cmd", "title": "Открыть", "group": "capability", "control": "button",
                 "management": "w"},
                {"name": "close_cmd", "title": "Закрыть", "group": "capability", "control": "button",
                 "management": "w"},
                {"name": "hold_time", "title": "Держать открытым", "group": "setting", "control": "counter",
                 "management": "rw", "unit": "с", "min": 0, "max": 300},
            ],
            "events": [
                {"name": "opened", "title": "Шлагбаум открыт", "when": {"signal": "state", "op": "==", "value": 2}},
                {"name": "jammed", "title": "Застревание", "when": {"signal": "alarm", "op": "==", "value": 1}},
            ],
        },
        "initial": {"state": 0, "obstacle": 0, "alarm": 0, "cycles": 0, "hold_time": 10},
    },
]

DEVICE_TYPES += [
    {
        "code": "valve", "title": "Клапан на воду", "family": "valve", "icon": "valve",
        "declaration": {
            "signals": [
                {"name": "valve", "title": "Кран", "group": "capability", "control": "switch", "management": "rw",
                 "values": _onoff("Закрыт", "Открыт"), "summary": True},
                {"name": "pressure", "title": "Давление", "group": "property", "control": "graph",
                 "management": "r", "unit": "бар"},
                {"name": "auto_close_s", "title": "Автозакрытие через", "group": "setting", "control": "counter",
                 "management": "rw", "unit": "с", "min": 0, "max": 3600},
            ],
            "events": [
                {"name": "closed", "title": "Кран закрыт", "when": {"signal": "valve", "op": "==", "value": 0}},
            ],
        },
        "initial": {"valve": 1, "pressure": 3.2, "auto_close_s": 0},
    },
    {
        "code": "fire", "title": "Пожарный датчик", "family": "fire", "icon": "fire",
        "declaration": {
            "signals": [
                {"name": "alarm", "title": "Пожар", "group": "property", "control": "list", "management": "r",
                 "values": _onoff("Нет", "Пожар"), "summary": True, "alarm_values": [1]},
                {"name": "smoke", "title": "Задымлённость", "group": "property", "control": "graph",
                 "management": "r", "unit": "%", "min": 0, "max": 100},
                {"name": "battery", "title": "Батарея", "group": "property", "control": "graph",
                 "management": "r", "unit": "%", "min": 0, "max": 100},
                {"name": "tamper", "title": "Вскрытие корпуса", "group": "property", "control": "list",
                 "management": "r", "values": _onoff("Нет", "Есть"), "alarm_values": [1]},
                {"name": "self_test", "title": "Самотест", "group": "capability", "control": "button",
                 "management": "w"},
                {"name": "threshold", "title": "Порог срабатывания", "group": "setting", "control": "counter",
                 "management": "rw", "unit": "%", "min": 10, "max": 95},
            ],
            "events": [
                {"name": "fire_detected", "title": "Обнаружен дым", "when": {"signal": "alarm", "op": "==", "value": 1}},
            ],
        },
        "initial": {"alarm": 0, "smoke": 5, "battery": 100, "tamper": 0, "threshold": 60},
    },
]

_BUY = "https://market.yandex.ru/search?text="
for _t, _q in {"leak": "умный датчик протечки", "counter": "умный счётчик воды с краном",
               "thermostat": "умный термостат", "light": "умная лампа", "barrier": "шлагбаум автоматический",
               "valve": "умный клапан перекрытия воды", "fire": "умный датчик дыма"}.items():
    next(d for d in DEVICE_TYPES if d["code"] == _t)["buy_url"] = _BUY + _q.replace(" ", "+")


_WATER = {"role": "water", "title": "Кран на воду", "types": ["valve", "counter"]}
_WATER_SIGNAL = {"valve": "valve", "counter": "load_relay"}
_ON_ERROR = {"retries": 3, "retry_delay_s": 2, "timeout_s": 3, "fallback": []}

SCENARIO_TEMPLATES = [
    {
        "code": "leak_protection", "title": "Защита от протечки",
        "description": "Протечка — кран перекроет воду, консьерж получит тревогу, вы — уведомление.",
        "room_types": ["bathroom", "toilet", "kitchen"],
        "requires": [{"role": "sensor", "title": "Датчик протечки", "types": ["leak"]}, _WATER],
        "rule": {
            "conditions": [
                {"type": "state", "role": "sensor", "signal": "leak", "op": "==", "value": 1},
            ],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "water", "signal": _WATER_SIGNAL, "value": 0},
                {"type": "notify", "audience": "concierge", "level": "alarm",
                 "text": "Протечка: {home} · {room}. Вода перекрыта"},
                {"type": "notify", "audience": "resident", "level": "alarm",
                 "text": "Протечка: {room}. Воду я перекрыл"},
            ],
            "on_error": {**_ON_ERROR, "fallback": [
                {"type": "notify", "audience": "concierge", "level": "alarm",
                 "text": "Кран не отвечает — перекройте воду вручную: {home}"},
                {"type": "notify", "audience": "resident", "level": "alarm",
                 "text": "Протечка: {room}. Кран не отвечает — консьерж уже предупреждён"}]},
            "cooldown_s": 60,
        },
        "keywords": ["протечк", "течь", "затоп", "залив", "вода", "кран", "клапан"],
    },
    {
        "code": "night_light", "title": "Ночной свет",
        "description": "Ночью свет включается на 30 %, чтобы не слепить.",
        "room_types": ["bathroom", "toilet", "hallway"],
        "requires": [{"role": "light", "title": "Светильник", "types": ["light"]}],
        "rule": {
            "conditions": [
                {"type": "state", "role": "light", "signal": "lamp", "op": "==", "value": 1},
                {"type": "mode", "op": "==", "value": "night"},
            ],
            "logic": "and",
            "actions": [{"type": "command", "role": "light", "signal": "brightness", "value": 30}],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["ночь", "ночн", "яркост", "не слеп", "приглуш"],
    },
    {
        "code": "battery_low", "title": "Батарея датчика села",
        "description": "Батарея датчика протечки ниже 20 % — напомним заменить.",
        "room_types": ["bathroom", "toilet", "kitchen"],
        "requires": [{"role": "sensor", "title": "Датчик протечки", "types": ["leak"]}],
        "rule": {
            "conditions": [
                {"type": "state", "role": "sensor", "signal": "battery", "op": "<", "value": 20},
            ],
            "logic": "and",
            "actions": [{"type": "notify", "audience": "resident", "level": "warning",
                         "text": "Датчик протечки ({room}): батарея садится, замените"}],
            "on_error": _ON_ERROR, "cooldown_s": 86400,
        },
        "keywords": ["батаре", "заряд", "сел"],
    },
    {
        "code": "tamper_alert", "title": "Датчик вскрыт",
        "description": "Корпус датчика протечки вскрыли — консьерж узнает.",
        "room_types": ["bathroom", "kitchen"],
        "requires": [{"role": "sensor", "title": "Датчик протечки", "types": ["leak"]}],
        "rule": {
            "conditions": [
                {"type": "state", "role": "sensor", "signal": "tamper", "op": "==", "value": 1},
            ],
            "logic": "and",
            "actions": [{"type": "notify", "audience": "concierge", "level": "warning",
                         "text": "Вскрыт датчик протечки: {home} · {room}"}],
            "on_error": _ON_ERROR, "cooldown_s": 600,
        },
        "keywords": ["вскрыт", "вскрыл", "тампер", "сняли"],
    },
    {
        "code": "kitchen_fire", "title": "Пожар на кухне",
        "description": "Дым выше порога — тревога консьержу и вам.",
        "room_types": ["kitchen"],
        "requires": [{"role": "smoke", "title": "Пожарный датчик", "types": ["fire"]}],
        "rule": {
            "conditions": [
                {"type": "state", "role": "smoke", "signal": "alarm", "op": "==", "value": 1},
            ],
            "logic": "and",
            "actions": [
                {"type": "notify", "audience": "concierge", "level": "alarm", "text": "Пожар: {home} · {room}"},
                {"type": "notify", "audience": "resident", "level": "alarm",
                 "text": "Дым на кухне! Консьерж уже знает"},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 300,
        },
        "keywords": ["пожар", "дым", "гор", "огонь"],
    },
    {
        "code": "away_water", "title": "Вода, когда ушёл",
        "description": "Режим «Ушёл» — кран перекрывается.",
        "room_types": ["kitchen"],
        "requires": [_WATER],
        "rule": {
            "conditions": [
                {"type": "mode", "op": "==", "value": "away"},
            ],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "water", "signal": _WATER_SIGNAL, "value": 0},
                {"type": "notify", "audience": "resident", "level": "info", "text": "Вы ушли — воду перекрыл"},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["ушёл", "ушел", "ухожу", "перекр", "вода"],
    },
    {
        "code": "warm_home", "title": "Тепло к приходу",
        "description": "Режим «Дома» — термостат на 22 °C.",
        "room_types": ["bedroom", "living"],
        "requires": [{"role": "thermo", "title": "Термостат", "types": ["thermostat"]}],
        "rule": {
            "conditions": [
                {"type": "mode", "op": "==", "value": "home"},
            ],
            "logic": "and",
            "actions": [{"type": "command", "role": "thermo", "signal": "target_temp", "value": 22}],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["тепло", "прихож", "вернул", "температур", "отоплен"],
    },
    {
        "code": "eco_away", "title": "Экономия, когда ушёл",
        "description": "Режим «Ушёл» — термостат на 18 °C.",
        "room_types": ["bedroom", "living"],
        "requires": [{"role": "thermo", "title": "Термостат", "types": ["thermostat"]}],
        "rule": {
            "conditions": [
                {"type": "mode", "op": "==", "value": "away"},
            ],
            "logic": "and",
            "actions": [{"type": "command", "role": "thermo", "signal": "target_temp", "value": 18}],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["эконом", "ушёл", "ушел", "сбер", "температур"],
    },
    {
        "code": "night_mode", "title": "Ночной режим",
        "description": "Режим «Ночь» — свет выключается, термостат на 20 °C.",
        "room_types": ["bedroom"],
        "requires": [{"role": "light", "title": "Светильник", "types": ["light"]},
                     {"role": "thermo", "title": "Термостат", "types": ["thermostat"]}],
        "rule": {
            "conditions": [
                {"type": "mode", "op": "==", "value": "night"},
            ],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "light", "signal": "lamp", "value": 0},
                {"type": "command", "role": "thermo", "signal": "target_temp", "value": 20},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["ночь", "спать", "сон", "отбой"],
    },
    {
        "code": "evening_light", "title": "Свет вечером",
        "description": "Каждый день в 19:00 включается свет.",
        "room_types": ["living"],
        "requires": [{"role": "light", "title": "Светильник", "types": ["light"]}],
        "rule": {
            "conditions": [
                {"type": "time", "op": ">=", "value": "19:00"},
            ],
            "logic": "and",
            "actions": [{"type": "command", "role": "light", "signal": "lamp", "value": 1}],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["вечер", "расписан", "19", "темнеет"],
    },
    {
        "code": "welcome_light", "title": "Свет при возвращении",
        "description": "Режим «Дома» — включается свет в коридоре.",
        "room_types": ["hallway"],
        "requires": [{"role": "light", "title": "Светильник", "types": ["light"]}],
        "rule": {
            "conditions": [
                {"type": "mode", "op": "==", "value": "home"},
            ],
            "logic": "and",
            "actions": [{"type": "command", "role": "light", "signal": "lamp", "value": 1}],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["пришёл", "пришел", "вернул", "коридор", "прихож"],
    },
    {
        "code": "leave_home", "title": "Я ушёл",
        "description": "Выключение света и бытовых приборов, вода перекрыта, отопление — на экономию.",
        "room_types": [],
        "requires": [{"role": "lights", "title": "Светильники", "types": ["light"], "multi": True, "optional": True},
                     {**_WATER, "optional": True},
                     {"role": "thermo", "title": "Термостат", "types": ["thermostat"], "optional": True}],
        "rule": {
            "conditions": [{"type": "mode", "op": "==", "value": "away"}],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "lights", "signal": "lamp", "value": 0},
                {"type": "command", "role": "water", "signal": _WATER_SIGNAL, "value": 0},
                {"type": "command", "role": "thermo", "signal": "target_temp", "value": 18},
                {"type": "notify", "audience": "resident", "level": "info",
                 "text": "Вы ушли: свет выключен, вода перекрыта"},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["ушёл", "ушел", "ухожу", "уход", "выключ", "никого"],
    },
    {
        "code": "i_am_home", "title": "Я дома",
        "description": "Включение комфортного режима: вода открыта, тепло, свет.",
        "room_types": [],
        "requires": [{**_WATER, "optional": True},
                     {"role": "thermo", "title": "Термостат", "types": ["thermostat"], "optional": True},
                     {"role": "lights", "title": "Светильники", "types": ["light"], "multi": True, "optional": True}],
        "rule": {
            "conditions": [{"type": "mode", "op": "==", "value": "home"}],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "water", "signal": _WATER_SIGNAL, "value": 1},
                {"type": "command", "role": "thermo", "signal": "target_temp", "value": 22},
                {"type": "command", "role": "lights", "signal": "lamp", "value": 1},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["пришёл", "пришел", "дома", "вернул", "комфорт", "тепло"],
    },
    {
        "code": "good_night", "title": "Спокойной ночи",
        "description": "Подготовка дома ко сну: свет выключен, термостат на 20 °C.",
        "room_types": [],
        "requires": [{"role": "lights", "title": "Светильники", "types": ["light"], "multi": True, "optional": True},
                     {"role": "thermo", "title": "Термостат", "types": ["thermostat"], "optional": True}],
        "rule": {
            "conditions": [{"type": "mode", "op": "==", "value": "night"}],
            "logic": "and",
            "actions": [
                {"type": "command", "role": "lights", "signal": "lamp", "value": 0},
                {"type": "command", "role": "thermo", "signal": "target_temp", "value": 20},
            ],
            "on_error": _ON_ERROR, "cooldown_s": 0,
        },
        "keywords": ["спокойной", "спать", "сон", "отбой", "ночь"],
    },
    {
        "code": "barrier_jam", "title": "Шлагбаум застрял",
        "description": "Авария шлагбаума — консьерж узнает сразу.",
        "room_types": ["outdoor"],
        "requires": [{"role": "barrier", "title": "Шлагбаум", "types": ["barrier"]}],
        "rule": {
            "conditions": [
                {"type": "state", "role": "barrier", "signal": "alarm", "op": "==", "value": 1},
            ],
            "logic": "and",
            "actions": [{"type": "notify", "audience": "concierge", "level": "alarm",
                         "text": "Шлагбаум застрял: {home}"}],
            "on_error": _ON_ERROR, "cooldown_s": 300,
        },
        "keywords": ["шлагбаум", "застрял", "парков", "двор"],
    },
]

HOME_SCENARIO_CODES = ["leave_home", "i_am_home", "good_night"]

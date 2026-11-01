from app.schemas import scenario as schemas
from app.services import devices as dev

DEFAULT_ON_ERROR = {
    "retries": 3, "retry_delay_s": 2, "timeout_s": 3,
    "fallback": [{"type": "notify", "audience": "resident", "level": "warning",
                  "text": "Сценарий не выполнился: устройство не отвечает"}],
}


class Checker:
    def __init__(self, home, scenario_id=None):
        self.home = home
        self.scenario_id = scenario_id
        self.devices = {d.id: d for d in home.devices}
        self.errors = []
        self.warnings = []

    def error(self, path, code, message):
        self.errors.append(schemas.Issue(path=path, code=code, message=message))

    def device(self, path, device_id):
        d = self.devices.get(device_id)
        if d is None:
            self.error(path, "not_found", f"Устройства {device_id} нет в этом доме")
        elif not d.online:
            self.warnings.append(schemas.Issue(path=path, code="device_offline",
                                               message=f"«{d.title}» сейчас не в сети"))
        return d

    def condition(self, p, c):
        if c.type not in ("state", "event"):
            return
        d = self.device(f"{p}.device_id", c.device_id)
        if d is None:
            return
        if c.type == "event":
            if dev.find_event(d.device_type, c.event) is None:
                self.error(f"{p}.event", "validation_error", f"У «{d.title}» нет события «{c.event}»")
            return
        sig = dev.find_signal(d.device_type, c.signal)
        if sig is None or sig.get("management") == "w":
            self.error(f"{p}.signal", "validation_error", f"У «{d.title}» нет значения «{c.signal}» для условия")
        elif c.op in ("==", "!="):
            problem = dev.check_value(sig, c.value)
            if problem:
                self.error(f"{p}.value", *problem)
        elif isinstance(c.value, bool) or not isinstance(c.value, (int, float)):
            self.error(f"{p}.value", "validation_error", f"«{sig['title']}»: для {c.op} нужно число")

    def action(self, p, a):
        if a.type != "command":
            return
        d = self.device(f"{p}.device_id", a.device_id)
        if d is None:
            return
        sig = dev.find_signal(d.device_type, a.signal)
        if sig is None:
            self.error(f"{p}.signal", "validation_error", f"У «{d.title}» нет команды «{a.signal}»")
            return
        if not dev.writable(sig):
            self.error(f"{p}.signal", "signal_readonly", f"«{sig['title']}» у «{d.title}» только для чтения")
            return
        problem = dev.check_value(sig, a.value)
        if problem:
            self.error(f"{p}.value", *problem)

    def conflicts(self, actions):
        mine = {(a.device_id, a.signal): a.value for a in actions if a.type == "command"}
        for other in self.home.scenarios:
            if other.id == self.scenario_id or not other.enabled:
                continue
            clash = next((a for a in other.actions if a.get("type") == "command"
                          and (a.get("device_id"), a.get("signal")) in mine
                          and mine[(a.get("device_id"), a.get("signal"))] != a.get("value")), None)
            if clash:
                d = self.devices.get(clash.get("device_id"))
                name = d.title if d else clash.get("device_id")
                self.warnings.append(schemas.Issue(
                    path="actions", code="scenario_conflict", scenario_id=other.id,
                    message=f"Сценарий «{other.title}» тоже управляет «{name}» "
                            f"({clash.get('signal')} = {clash.get('value')})"))


def validate(body, home, scenario_id=None):
    check = Checker(home, scenario_id)
    for i, c in enumerate(body.conditions):
        check.condition(f"conditions[{i}]", c)
    for i, a in enumerate(body.actions):
        check.action(f"actions[{i}]", a)
    check.conflicts(body.actions)
    return check.errors, check.warnings


def to_fields(body):
    return {
        "title": body.title,
        "description": body.description,
        "enabled": body.enabled,
        "conditions": [c.model_dump() for c in body.conditions],
        "logic": body.logic,
        "actions": [a.model_dump() for a in body.actions],
        "on_error": body.on_error.model_dump() if body.on_error else dict(DEFAULT_ON_ERROR),
        "cooldown_s": body.cooldown_s,
    }

from typing import Any

CONTINUOUS = {"battery", "total", "flow", "power_w", "energy_kwh", "temperature", "humidity", "pressure", "smoke"}

AMBIENT = 20.0
MEM: dict[int, dict[str, Any]] = {}


def _num(state, name, default=0.0):
    v = state.get(name, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return default
    return float(v)


def _battery(state, rate, dt, digits=3):
    return max(0.0, round(_num(state, "battery", 100) - rate * dt, digits))


def _leak(state, mem, dt, n, now):
    return {"battery": _battery(state, 0.002, dt)}


def _counter(state, mem, dt, n, now):
    flow = 0.0
    if state.get("load_relay") == 1 and n % 6 < 3:
        flow = 0.36
    u = {"flow": flow, "battery": _battery(state, 0.0005, dt, 4)}
    if flow:
        u["total"] = round(_num(state, "total") + flow * dt / 3600, 4)
    return u


def _thermostat_output(state, temp, target):
    mode, output = state.get("mode", 3), state.get("output", 0)
    if state.get("fault") == 1 or mode == 0:
        return 0
    if output == 1 and temp >= target or output == 2 and temp <= target:
        return 0
    if output == 0 and mode in (1, 3) and temp <= target - 0.5:
        return 1
    if output == 0 and mode in (2, 3) and temp >= target + 0.5:
        return 2
    return output


def _thermostat(state, mem, dt, n, now):
    temp = _num(state, "temperature", AMBIENT)
    output = _thermostat_output(state, temp, _num(state, "target_temp", 22))
    if output == 1:
        temp += 0.05 * dt
    elif output == 2:
        temp -= 0.05 * dt
    else:
        temp += (AMBIENT - temp) * 0.002 * dt
    return {"temperature": round(temp, 1), "output": output, "humidity": 43 + n % 5}


def _light(state, mem, dt, n, now):
    if state.get("lamp") != 1:
        mem.pop("on_since", None)
        return {"power_w": 0.0}
    power = round(12 * _num(state, "brightness", 100) / 100, 1)
    u = {"power_w": power, "energy_kwh": round(_num(state, "energy_kwh") + power * dt / 3.6e6, 6)}
    timeout = _num(state, "offline_timeout")
    if timeout > 0 and now - mem.setdefault("on_since", now) >= timeout:
        u["lamp"], u["power_w"] = 0, 0.0
        mem.pop("on_since", None)
    return u


def _barrier(state, mem, dt, n, now):
    st, obstacle = state.get("state", 0), state.get("obstacle", 0)
    if st == 1:
        mem["open_since"] = now
        return {"state": 2, "cycles": int(_num(state, "cycles")) + 1}
    if st == 2 and now - mem.setdefault("open_since", now) >= _num(state, "hold_time", 10):
        return {"state": 4 if obstacle else 3}
    if st == 4 and not obstacle:
        return {"state": 3}
    if st == 3:
        if obstacle:
            mem["open_since"] = now
        return {"state": 2 if obstacle else 0}
    return {}


def _valve(state, mem, dt, n, now):
    if state.get("valve") != 1:
        return {"pressure": 0.0}
    return {"pressure": round(3.2 + (n % 3) * 0.05, 2)}


def _fire(state, mem, dt, n, now):
    smoke = _num(state, "smoke", 5)
    if smoke > 5:
        smoke = max(5.0, smoke - 1)
    return {
        "smoke": smoke,
        "alarm": int(smoke >= _num(state, "threshold", 60)),
        "battery": _battery(state, 0.001, dt),
    }


TICKS = {
    "leak": _leak,
    "counter": _counter,
    "thermostat": _thermostat,
    "light": _light,
    "barrier": _barrier,
    "valve": _valve,
    "fire": _fire,
}


def _changed(state, updates):
    return {k: v for k, v in updates.items() if state.get(k) != v}


def tick(family, device_id, state, dt, n, now):
    fn = TICKS.get(family)
    if fn is None:
        return {}
    return _changed(state, fn(state, MEM.setdefault(device_id, {}), dt, n, now))


def react(family, device_id, state, signal, value, now):
    mem = MEM.setdefault(device_id, {})
    u = {}
    if family == "barrier" and signal == "open_cmd" and state.get("state") in (0, 3):
        u["state"] = 1
    elif family == "barrier" and signal == "close_cmd" and state.get("state") in (2, 4):
        u["state"] = 3
    elif family == "light" and signal in ("lamp", "brightness"):
        u = _light_power(state, mem, signal, now)
    elif family == "counter" and signal == "load_relay" and value == 0:
        u["flow"] = 0.0
    elif family == "valve" and signal == "valve":
        u["pressure"] = 3.2 if value == 1 else 0.0
    elif family == "fire" and signal in ("smoke", "threshold"):
        u["alarm"] = int(_num(state, "smoke", 5) >= _num(state, "threshold", 60))
    return _changed(state, u)


def _light_power(state, mem, signal, now):
    on = state.get("lamp") == 1
    if signal == "lamp" and on:
        mem["on_since"] = now
    elif signal == "lamp":
        mem.pop("on_since", None)
    return {"power_w": round(12 * _num(state, "brightness", 100) / 100, 1) if on else 0.0}

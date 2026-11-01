def duplicates(names):
    return sorted({n for n in names if names.count(n) > 1})


def signal_problems(s):
    out = []
    if s.group == "capability" and s.management == "r":
        out.append(f"«{s.title}»: команда не может быть только для чтения (management rw или w)")
    if s.control == "button" and s.management != "w":
        out.append(f"«{s.title}»: кнопка — management w")
    if s.control == "range" and (s.min is None or s.max is None):
        out.append(f"«{s.title}»: у ползунка нужны min и max")
    if s.min is not None and s.max is not None and s.min > s.max:
        out.append(f"«{s.title}»: min больше max")
    if s.control == "list" and not s.values:
        out.append(f"«{s.title}»: у списка нужны values")
    return out


def problems(decl):
    names = [s.name for s in decl.signals]
    errors = [f"сигнал «{n}» повторяется" for n in duplicates(names)]
    for s in decl.signals:
        errors += signal_problems(s)
    errors += [f"событие «{n}» повторяется" for n in duplicates([e.name for e in decl.events])]
    errors += [f"событие «{e.title}» ссылается на несуществующий сигнал «{e.when.signal}»"
               for e in decl.events if e.when.signal not in names]
    return errors


def default_value(s):
    if s.get("values"):
        return s["values"][0]["value"]
    if s.get("min") is not None:
        return s["min"]
    return "" if s.get("control") == "text" else 0


def defaults(decl):
    return {s["name"]: default_value(s) for s in decl.get("signals", []) if s.get("management") != "w"}

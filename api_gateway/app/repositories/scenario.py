from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import session_manager
from app.models import Device, DeviceType, Home, Room, Scenario, ScenarioTemplate
from app.repositories.home import _last_runs, _load_home
from app.schemas import scenario as schemas
from app.services import devices as dev
from app.services import templates as tpl_svc
from app.services import validation
from app.services.engine import engine
from app.services.errors import ApiError, not_found

MODES = [("home", "Дома"), ("away", "Ушёл"), ("night", "Ночь")]


def scenario_out(s: Scenario, last_run: str | None = None) -> schemas.ScenarioOut:
    return schemas.ScenarioOut(
        id=s.id, home_id=s.home_id, title=s.title, description=s.description, enabled=s.enabled, source=s.source,
        template_id=s.template_id, cooldown_s=s.cooldown_s, conditions=s.conditions, logic=s.logic,
        actions=s.actions, on_error=s.on_error, last_run=last_run,
    )


async def _load_scenario(session: AsyncSession, scenario_id: int, user_id: int) -> tuple[Scenario, Home]:
    s = await session.get(Scenario, scenario_id)
    if s is None:
        raise not_found("Сценарий", scenario_id)
    try:
        home = await _load_home(session, s.home_id, user_id)
    except ApiError:
        raise not_found("Сценарий", scenario_id) from None
    return s, home


def _raise_if_errors(errors: list[schemas.Issue]) -> None:
    if errors:
        raise ApiError(422, "validation_error", "Сценарий не прошёл проверку",
                       {"errors": [e.model_dump(exclude_none=True) for e in errors]})


def _catalog_signal(sig: dict) -> schemas.CatalogSignal:
    return schemas.CatalogSignal(name=sig["name"], title=sig["title"], control=sig.get("control", "text"),
                                 unit=sig.get("unit"), min=sig.get("min"), max=sig.get("max"),
                                 values=sig.get("values"))


class ScenarioRepository:
    async def templates_for_home(self, home_id: int, user_id: int) -> list[schemas.TemplateOut]:
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            types = {t.code: t for t in await session.scalars(select(DeviceType))}
            templates = await session.scalars(select(ScenarioTemplate).order_by(ScenarioTemplate.id))
            return [tpl_svc.template_out(home, t, types) for t in templates if tpl_svc.visible(home, t)]

    async def create_from_template(self, user_id: int, body: schemas.FromTemplateIn,
                                   source: str = "template") -> schemas.FromTemplateOut:
        async with session_manager() as session:
            home = await _load_home(session, body.home_id, user_id)
            tpl = await session.get(ScenarioTemplate, body.template_id)
            if tpl is None:
                raise not_found("Заготовка", body.template_id)
            room = None
            if body.room_id is not None:
                room = await session.get(Room, body.room_id)
                if room is None or room.home_id != home.id:
                    raise not_found("Комната", body.room_id)

            bindings, missing = tpl_svc.bind(home, tpl, room)
            created: list[Device] = []
            if missing:
                if not body.add_virtual_missing:
                    raise ApiError(409, "missing_devices", "Не хватает устройств для сценария",
                                   {"missing": [{"role": s["role"], "title": s["title"], "type": s["types"][0]}
                                                for s in missing]})
                types = {t.code: t for t in await session.scalars(select(DeviceType))}
                target = tpl_svc.virtual_room(home, tpl, room)
                for spec in missing:
                    dtype = types[spec["types"][0]]
                    device = Device(home_id=home.id, room_id=target.id if target else None, device_type=dtype,
                                    title=dtype.title, mode="virtual", online=True,
                                    state=dict(dtype.declaration.get("defaults", {})))
                    session.add(device)
                    created.append(device)
                    bindings[spec["role"]] = [device]
                await session.flush()

            scenario = Scenario(home_id=home.id, **{**tpl_svc.build_scenario(tpl, bindings, room), "source": source})
            session.add(scenario)
            await session.commit()
            out = schemas.FromTemplateOut(scenario=scenario_out(scenario), created_devices=[d.id for d in created])
        await engine.prime(out.scenario.id)
        return out


    async def list_for_home(self, home_id: int, user_id: int) -> list[schemas.ScenarioOut]:
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            scenarios = sorted(home.scenarios, key=lambda s: s.id)
            last = await _last_runs(session, [s.id for s in scenarios])
            return [scenario_out(s, last.get(s.id)) for s in scenarios]

    async def get(self, scenario_id: int, user_id: int) -> schemas.ScenarioOut:
        async with session_manager() as session:
            s, _ = await _load_scenario(session, scenario_id, user_id)
            last = await _last_runs(session, [s.id])
            return scenario_out(s, last.get(s.id))

    async def validate(self, user_id: int, body: schemas.ScenarioValidateIn) -> schemas.ValidateOut:
        async with session_manager() as session:
            home = await _load_home(session, body.home_id, user_id)
            errors, warnings = validation.validate(body, home, body.scenario_id)
            return schemas.ValidateOut(ok=not errors, errors=errors, warnings=warnings)

    async def create(self, user_id: int, body: schemas.ScenarioCreate) -> schemas.ScenarioOut:
        async with session_manager() as session:
            home = await _load_home(session, body.home_id, user_id)
            errors, _ = validation.validate(body, home)
            _raise_if_errors(errors)
            s = Scenario(home_id=home.id, source="manual", **validation.to_fields(body))
            session.add(s)
            await session.commit()
            out = scenario_out(s)
        await engine.prime(out.id)
        return out

    async def update(self, scenario_id: int, user_id: int, body: schemas.ScenarioBody) -> schemas.ScenarioOut:
        async with session_manager() as session:
            s, home = await _load_scenario(session, scenario_id, user_id)
            errors, _ = validation.validate(body, home, s.id)
            _raise_if_errors(errors)
            for k, v in validation.to_fields(body).items():
                setattr(s, k, v)
            engine.forget(s.id)
            await session.commit()
            last = await _last_runs(session, [s.id])
            out = scenario_out(s, last.get(s.id))
        await engine.prime(out.id)
        return out

    async def patch(self, scenario_id: int, user_id: int, body: schemas.ScenarioPatch) -> schemas.ScenarioOut:
        async with session_manager() as session:
            s, home = await _load_scenario(session, scenario_id, user_id)
            if body.enabled and not s.enabled:
                stored = schemas.ScenarioBody.model_validate({
                    "title": s.title, "description": s.description, "conditions": s.conditions, "logic": s.logic,
                    "actions": s.actions, "cooldown_s": s.cooldown_s})
                errors, _ = validation.validate(stored, home, s.id)
                _raise_if_errors(errors)
            for k, v in body.model_dump(exclude_none=True).items():
                setattr(s, k, v)
            engine.forget(s.id)
            await session.commit()
            last = await _last_runs(session, [s.id])
            out = scenario_out(s, last.get(s.id))
        await engine.prime(out.id)
        return out

    async def delete(self, scenario_id: int, user_id: int) -> None:
        async with session_manager() as session:
            s, _ = await _load_scenario(session, scenario_id, user_id)
            await session.delete(s)
            await session.commit()

    async def editor_catalog(self, home_id: int, user_id: int) -> schemas.EditorCatalog:
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            rooms = {r.id: r.title for r in home.rooms}
            devices = []
            for d in sorted(home.devices, key=lambda d: d.id):
                sigs = dev.signals(d.device_type)
                devices.append(schemas.CatalogDevice(
                    id=d.id, title=d.title, room=rooms.get(d.room_id), type=d.device_type.code,
                    icon=d.device_type.icon, online=d.online,
                    states=[_catalog_signal(s) for s in sigs if dev.readable(s)],
                    events=[{"name": e["name"], "title": e["title"]}
                            for e in (d.device_type.declaration or {}).get("events", [])],
                    commands=[_catalog_signal(s) for s in sigs if dev.writable(s)],
                ))
            C = schemas.Choice
            return schemas.EditorCatalog(
                devices=devices,
                condition_types=[C(value="state", title="Значение устройства"), C(value="event", title="Событие"),
                                 C(value="mode", title="Режим дома"), C(value="time", title="Время")],
                action_types=[C(value="command", title="Команда устройству"),
                              C(value="notify", title="Уведомление"), C(value="delay", title="Пауза")],
                ops=["==", "!=", ">", ">=", "<", "<="],
                modes=[C(value=v, title=t) for v, t in MODES],
                audiences=[C(value="resident", title="Жителю"), C(value="concierge", title="Консьержу")],
                levels=[C(value="info", title="Обычное"), C(value="warning", title="Внимание"),
                        C(value="alarm", title="Тревога")],
            )

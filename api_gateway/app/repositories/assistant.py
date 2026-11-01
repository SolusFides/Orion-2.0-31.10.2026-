from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import iso, session_manager
from app.models import ChatMessage, ChatSession, DeviceType, Home, ScenarioTemplate
from app.repositories.home import _load_home
from app.repositories.scenario import ScenarioRepository
from app.schemas import assistant as schemas
from app.schemas.scenario import FromTemplateIn
from app.services import assistant as svc
from app.services.errors import ApiError, not_found


def _msg(m: ChatMessage) -> schemas.MessageOut:
    return schemas.MessageOut(id=m.id, role=m.role, text=m.text, proposal=m.proposal, engine=m.engine,
                              created_at=iso(m.created_at))


class AssistantRepository:
    async def message(self, user_id: int, body: schemas.AssistantIn) -> schemas.AssistantReply:
        async with session_manager() as session:
            home = await _load_home(session, body.home_id, user_id)
            if body.session_id is not None:
                chat = await session.get(ChatSession, body.session_id)
                if chat is None or chat.home_id != home.id:
                    raise not_found("Диалог", body.session_id)
            else:
                chat = ChatSession(home_id=home.id)
                session.add(chat)
                await session.flush()
            session.add(ChatMessage(session_id=chat.id, role="user", text=body.text))
            templates = list(await session.scalars(select(ScenarioTemplate).order_by(ScenarioTemplate.id)))
            types = {t.code: t for t in await session.scalars(select(DeviceType))}
            proposal, reply, suggestions = await svc.propose(body.text, home, templates, types)
            msg = ChatMessage(session_id=chat.id, role="assistant", text=reply, proposal=proposal,
                              engine=proposal["engine"] if proposal else "keywords")
            session.add(msg)
            await session.commit()
            return schemas.AssistantReply(session_id=chat.id, message=_msg(msg), proposal=proposal,
                                          suggestions=suggestions)

    async def session(self, session_id: int, user_id: int) -> schemas.SessionOut:
        async with session_manager() as session:
            chat = await session.scalar(select(ChatSession).where(ChatSession.id == session_id)
                                        .options(selectinload(ChatSession.messages)))
            home = await session.get(Home, chat.home_id) if chat else None
            if chat is None or home is None or home.user_id != user_id:
                raise not_found("Диалог", session_id)
            return schemas.SessionOut(id=chat.id, home_id=chat.home_id, messages=[_msg(m) for m in chat.messages])

    async def accept(self, message_id: int, user_id: int, body: schemas.AcceptIn) -> schemas.AcceptOut:
        async with session_manager() as session:
            msg = await session.get(ChatMessage, message_id)
            chat = await session.get(ChatSession, msg.session_id) if msg else None
            home = await session.get(Home, chat.home_id) if chat else None
            if msg is None or home is None or home.user_id != user_id or not msg.proposal:
                raise not_found("Предложение", message_id)
            proposal = msg.proposal
            home_id = home.id
        room_id = body.room_id or (proposal.get("room") or {}).get("id")
        if body.edit:
            if not proposal.get("ready") or not proposal.get("scenario"):
                raise ApiError(409, "missing_devices", "Не хватает устройств — примите с виртуальными",
                               {"missing": proposal.get("missing", [])})
            s = proposal["scenario"]
            return schemas.AcceptOut(draft={"home_id": home_id, **{k: s[k] for k in (
                "title", "description", "conditions", "logic", "actions", "on_error", "cooldown_s")}})
        out = await ScenarioRepository().create_from_template(
            user_id, FromTemplateIn(home_id=home_id, template_id=proposal["template_id"], room_id=room_id,
                                    add_virtual_missing=body.add_virtual_missing), source="assistant")
        async with session_manager() as session:
            msg = await session.get(ChatMessage, message_id)
            msg.accepted_scenario_id = out.scenario.id
            await session.commit()
        return schemas.AcceptOut(scenario=out.scenario, created_devices=out.created_devices)



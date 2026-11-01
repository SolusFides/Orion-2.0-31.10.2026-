from sqlalchemy import select

from app.database import iso, session_manager, utcnow
from app.models import Home, Notification, User
from app.repositories.home import _load_home
from app.schemas import notification as schemas
from app.services.errors import ApiError, not_found
from app.services.sse import CONCIERGE, home_channel, hub


def _out(n: Notification, home: Home) -> schemas.NotificationOut:
    return schemas.NotificationOut(
        id=n.id, home=schemas.HomeBrief(id=home.id, title=home.title, address=home.address), run_id=n.run_id,
        audience=n.audience, level=n.level, title=n.title, text=n.text, status=n.status,
        created_at=iso(n.created_at),
    )


class NotificationRepository:
    async def for_home(self, home_id: int, user_id: int, limit: int) -> list[schemas.NotificationOut]:
        async with session_manager() as session:
            home = await _load_home(session, home_id, user_id)
            rows = await session.scalars(
                select(Notification).where(Notification.home_id == home_id, Notification.audience == "resident")
                .order_by(Notification.id.desc()).limit(limit)
            )
            return [_out(n, home) for n in rows]

    async def for_concierge(self, status: str | None, limit: int) -> list[schemas.NotificationOut]:
        async with session_manager() as session:
            q = select(Notification).where(Notification.audience == "concierge")
            if status:
                q = q.where(Notification.status == status)
            rows = list(await session.scalars(q.order_by(Notification.id.desc()).limit(limit)))
            homes = {h.id: h for h in await session.scalars(select(Home).where(Home.id.in_({n.home_id for n in rows})))}
            return [_out(n, homes[n.home_id]) for n in rows]

    async def read(self, notification_id: int, user: User) -> schemas.NotificationOut:
        async with session_manager() as session:
            n = await session.get(Notification, notification_id)
            home = await session.get(Home, n.home_id) if n else None
            if n is None or n.audience != "resident" or home is None or home.user_id != user.id:
                raise not_found("Уведомление", notification_id)
            if n.status == "new":
                n.status = "read"
            await session.commit()
            return _out(n, home)

    async def ack(self, notification_id: int, user: User) -> schemas.NotificationOut:
        async with session_manager() as session:
            n = await session.get(Notification, notification_id)
            if n is None or n.audience != "concierge":
                raise not_found("Уведомление", notification_id)
            if n.status == "acked":
                raise ApiError(409, "already_acked", "Уже принято")
            home = await session.get(Home, n.home_id)
            n.status, n.acked_by = "acked", user.id
            reply = Notification(home_id=n.home_id, run_id=n.run_id, audience="resident", level="info",
                                 title="Консьерж в курсе", text=f"Консьерж принял: {n.text}")
            session.add(reply)
            await session.commit()
            hub.publish(CONCIERGE, "notification_acked", {"id": n.id, "by": user.name, "at": iso(utcnow())})
            hub.publish(home_channel(n.home_id), "notification", {
                "id": reply.id, "home_id": n.home_id, "audience": "resident", "level": "info",
                "title": reply.title, "text": reply.text, "run_id": n.run_id, "at": iso(reply.created_at)})
            return _out(n, home)


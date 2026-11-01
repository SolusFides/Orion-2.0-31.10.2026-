from fastapi import APIRouter, Query, Request

from app.dependencies.auth import ConciergeStreamUser, ConciergeUser, CurrentUser
from app.repositories.notification import NotificationRepository
from app.schemas import notification as schemas
from app.services.sse import CONCIERGE, hub

router = APIRouter(prefix="/api", tags=["Notifications"])
repo = NotificationRepository()


@router.get("/homes/{home_id}/notifications", response_model=list[schemas.NotificationOut])
async def home_notifications(home_id: int, user: CurrentUser,
                             limit: int = Query(50, ge=1, le=200)) -> list[schemas.NotificationOut]:
    return await repo.for_home(home_id, user.id, limit)


@router.post("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
async def read_notification(notification_id: int, user: CurrentUser) -> schemas.NotificationOut:
    return await repo.read(notification_id, user)


@router.get("/concierge/notifications", response_model=list[schemas.NotificationOut])
async def concierge_notifications(_: ConciergeUser, status: str | None = Query(None),
                                  limit: int = Query(50, ge=1, le=200)) -> list[schemas.NotificationOut]:
    return await repo.for_concierge(status, limit)


@router.post("/notifications/{notification_id}/ack", response_model=schemas.NotificationOut)
async def ack_notification(notification_id: int, user: ConciergeUser) -> schemas.NotificationOut:
    return await repo.ack(notification_id, user)


@router.get("/concierge/stream")
async def concierge_stream(request: Request, _: ConciergeStreamUser):
    return hub.response(CONCIERGE, request)

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.database import iso, session_manager
from app.dependencies.auth import CurrentUser
from app.models import Device, UjinSyncLog
from app.services.ujin import publisher

router = APIRouter(prefix="/api/ujin", tags=["Ujin"])


@router.get("/status")
async def ujin_status(_: CurrentUser) -> dict[str, Any]:
    async with session_manager() as session:
        linked = await session.scalar(select(func.count(Device.id)).where(Device.mode == "ujin"))
    return {**publisher.status(), "linked_devices": linked or 0}


@router.get("/log")
async def ujin_log(_: CurrentUser, limit: int = Query(50, ge=1, le=200)) -> list[dict[str, Any]]:
    async with session_manager() as session:
        rows = await session.scalars(select(UjinSyncLog).order_by(UjinSyncLog.id.desc()).limit(limit))
        return [{"id": r.id, "direction": r.direction, "device_id": r.device_id, "method": r.method,
                 "payload": r.payload, "status": r.status, "error": r.error, "at": iso(r.at)} for r in rows]


@router.post("/sync")
async def ujin_sync(_: CurrentUser) -> dict[str, Any]:
    if not publisher.enabled:
        return {"enabled": False, "results": [], "hint": "UJIN_PUBLISH_ENABLED=true и UJIN_UST в .env"}
    return {"enabled": True, "results": await publisher.flush(full=True)}

from sqlalchemy import select

from app.database import session_manager
from app.models import RoomType


class RoomTypeRepository:
    async def list(self) -> list[RoomType]:
        async with session_manager() as session:
            return list(await session.scalars(select(RoomType).order_by(RoomType.sort)))

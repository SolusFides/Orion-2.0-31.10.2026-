from sqlalchemy import select

from app.database import session_manager
from app.models import User


class UserRepository:
    async def get_by_phone(self, phone: str) -> User | None:
        async with session_manager() as session:
            return await session.scalar(select(User).where(User.phone == phone))

    async def get_by_id(self, user_id: int) -> User | None:
        async with session_manager() as session:
            return await session.get(User, user_id)

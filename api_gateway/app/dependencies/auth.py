from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings
from app.dependencies.blacklist import BLACKLIST_TOKENS
from app.models import User
from app.repositories.user import UserRepository
from app.services.errors import ApiError, unauthorized

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
user_repo = UserRepository()


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


async def user_from_token(token: str | None) -> User:
    if not token:
        raise unauthorized()
    if token in BLACKLIST_TOKENS:
        raise unauthorized("Токен отозван (выход)", "token_revoked")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except ExpiredSignatureError:
        raise unauthorized("Срок токена истёк", "token_expired") from None
    except (JWTError, TypeError, ValueError):
        raise unauthorized("Неверный токен", "token_invalid") from None
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise unauthorized("Пользователь не найден")
    return user


async def token_required(token: Annotated[str | None, Depends(oauth2_scheme)]) -> User:
    return await user_from_token(token)


async def token_or_query(
    header_token: Annotated[str | None, Depends(oauth2_scheme)],
    token: Annotated[str | None, Query()] = None,
) -> User:
    return await user_from_token(header_token or token)


CurrentUser = Annotated[User, Depends(token_required)]
StreamUser = Annotated[User, Depends(token_or_query)]


async def concierge_required(user: Annotated[User, Depends(token_required)]) -> User:
    if user.role != "concierge":
        raise ApiError(403, "forbidden", "Только для консьержа")
    return user


async def concierge_stream(user: Annotated[User, Depends(token_or_query)]) -> User:
    if user.role != "concierge":
        raise ApiError(403, "forbidden", "Только для консьержа")
    return user


ConciergeUser = Annotated[User, Depends(concierge_required)]
ConciergeStreamUser = Annotated[User, Depends(concierge_stream)]

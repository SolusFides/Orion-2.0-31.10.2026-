from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies.auth import CurrentUser, create_access_token, oauth2_scheme
from app.dependencies.blacklist import BLACKLIST_TOKENS
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from app.services.errors import unauthorized
from app.services.security import check_password, normalize_phone

router = APIRouter(prefix="/api/auth", tags=["Auth"])
user_repo = UserRepository()


@router.post("/login", response_model=LoginResponse)
async def login(form: Annotated[LoginRequest, Depends(LoginRequest.as_form)]) -> LoginResponse:
    user = await user_repo.get_by_phone(normalize_phone(form.username))
    if user is None or not check_password(form.password, user.password_hash):
        raise unauthorized("Неверный телефон или пароль", "wrong_credentials")
    return LoginResponse(
        access_token=create_access_token(user.id), token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(_: CurrentUser, token: Annotated[str | None, Depends(oauth2_scheme)]) -> LogoutResponse:
    if token:
        BLACKLIST_TOKENS.add(token)
    return LogoutResponse(message="Вы вышли")

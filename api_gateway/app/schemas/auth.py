from fastapi import Form
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(cls, username: str = Form(...),
                password: str = Form(...)):
        return cls(username=username, password=password)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class LogoutResponse(BaseModel):
    message: str

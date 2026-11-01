from typing import Any

from app.config import settings


class LLMUnavailable(Exception):
    pass


async def propose(text: str, home_context: dict[str, Any]) -> dict[str, Any]:
    if not settings.GIGACHAT_AUTH_KEY:
        raise LLMUnavailable("ключ GigaChat не задан")
    raise LLMUnavailable("GigaChat ещё не подключён — заглушка")

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from fastapi.responses import StreamingResponse

log = logging.getLogger(__name__)

PING_S = 15.0
QUEUE_SIZE = 500


def home_channel(home_id: int) -> str:
    return f"home:{home_id}"


CONCIERGE = "concierge"


class SSEHub:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    def publish(self, channel: str, event: str, data: dict[str, Any]) -> None:
        msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
        for q in list(self._subs.get(channel, ())):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            q.put_nowait(msg)

    async def _stream(self, channel: str, request: Request) -> AsyncIterator[str]:
        q: asyncio.Queue[str] = asyncio.Queue(QUEUE_SIZE)
        self._subs[channel].add(q)
        try:
            yield ": connected\n\n"
            while not await request.is_disconnected():
                try:
                    yield await asyncio.wait_for(q.get(), timeout=PING_S)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            self._subs[channel].discard(q)
            if not self._subs[channel]:
                self._subs.pop(channel, None)

    def response(self, channel: str, request: Request) -> StreamingResponse:
        return StreamingResponse(
            self._stream(channel, request),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )


hub = SSEHub()

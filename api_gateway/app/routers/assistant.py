from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUser
from app.repositories.assistant import AssistantRepository
from app.schemas import assistant as schemas

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])
repo = AssistantRepository()


@router.post("/messages", response_model=schemas.AssistantReply)
async def send_message(body: schemas.AssistantIn, user: CurrentUser) -> schemas.AssistantReply:
    return await repo.message(user.id, body)


@router.get("/sessions/{session_id}", response_model=schemas.SessionOut)
async def get_session(session_id: int, user: CurrentUser) -> schemas.SessionOut:
    return await repo.session(session_id, user.id)


@router.post("/messages/{message_id}/accept", response_model=schemas.AcceptOut,
             status_code=status.HTTP_201_CREATED)
async def accept(message_id: int, body: schemas.AcceptIn, user: CurrentUser) -> schemas.AcceptOut:
    return await repo.accept(message_id, user.id, body)

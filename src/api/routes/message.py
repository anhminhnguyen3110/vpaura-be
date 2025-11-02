from fastapi import APIRouter, Depends, status
from ...services.message import MessageService
from ...schemas.message import MessageCreate, MessageResponse
from ...database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    request: MessageCreate,
    session: AsyncSession = Depends(get_db_session)
):
    service = MessageService(session)
    return await service.create_message(request)


@router.get("/session/{session_id}", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = MessageService(session)
    return await service.get_by_session(session_id)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = MessageService(session)
    await service.delete_message(message_id)

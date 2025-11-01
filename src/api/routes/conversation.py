from fastapi import APIRouter, Depends, status
from ...services.conversation import ConversationService
from ...schemas.conversation import ConversationCreate, ConversationResponse
from ...database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    session: AsyncSession = Depends(get_db_session)
):
    service = ConversationService(session)
    return await service.create_conversation(request)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = ConversationService(session)
    return await service.get_by_id(conversation_id)


@router.get("/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    service = ConversationService(session)
    return await service.get_by_user(user_id, skip, limit)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    service = ConversationService(session)
    await service.delete_conversation(conversation_id)

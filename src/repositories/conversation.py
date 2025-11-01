from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from ..models.conversation import Conversation


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def get_by_id(self, id: int) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == id)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.documents)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, entity: Conversation) -> Conversation:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: Conversation) -> Conversation:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        conversation = await self.get_by_id(id)
        if conversation:
            await self.session.delete(conversation)
            await self.session.flush()
            return True
        return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

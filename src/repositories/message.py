from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..models.message import Message


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def get_by_id(self, id: int) -> Optional[Message]:
        result = await self.session.execute(
            select(Message).where(Message.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_session_id(self, session_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, entity: Message) -> Message:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: Message) -> Message:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        message = await self.get_by_id(id)
        if message:
            await self.session.delete(message)
            await self.session.flush()
            return True
        return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Message]:
        result = await self.session.execute(
            select(Message).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

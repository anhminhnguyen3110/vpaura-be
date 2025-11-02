from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from ..models.session import Session


class SessionRepository(BaseRepository[Session]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def get_by_id(self, id: int) -> Optional[Session]:
        result = await self.session.execute(
            select(Session)
            .where(Session.id == id)
            .options(
                selectinload(Session.messages),
                selectinload(Session.documents)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Session]:
        result = await self.session.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, entity: Session) -> Session:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: Session) -> Session:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        session_obj = await self.get_by_id(id)
        if session_obj:
            await self.session.delete(session_obj)
            await self.session.flush()
            return True
        return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Session]:
        result = await self.session.execute(
            select(Session).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

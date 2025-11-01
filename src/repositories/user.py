from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def get_by_id(self, id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, entity: User) -> User:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: User) -> User:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        user = await self.get_by_id(id)
        if user:
            await self.session.delete(user)
            await self.session.flush()
            return True
        return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

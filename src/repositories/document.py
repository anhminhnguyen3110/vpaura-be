from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from ..models.document import Document


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def get_by_id(self, id: int) -> Optional[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == id)
            .options(selectinload(Document.threads))
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_thread_id(self, thread_id: int) -> List[Document]:
        result = await self.session.execute(
            select(Document)
            .join(Document.threads)
            .where(Document.threads.any(id=thread_id))
        )
        return list(result.scalars().all())
    
    async def create(self, entity: Document) -> Document:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: Document) -> Document:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        document = await self.get_by_id(id)
        if document:
            await self.session.delete(document)
            await self.session.flush()
            return True
        return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        result = await self.session.execute(
            select(Document).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

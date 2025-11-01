from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

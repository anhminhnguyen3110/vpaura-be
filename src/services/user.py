"""User service for managing user operations."""

from ..repositories.user import UserRepository
from ..schemas.user import UserCreate, UserResponse
from ..models.user import User
from ..exceptions.base import NotFoundException
from ..constants.messages import Messages
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        user = User(
            email=user_data.email,
            username=user_data.username
        )
        
        created = await self.repository.create(user)
        return UserResponse.model_validate(created)
    
    async def get_by_id(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(Messages.USER_NOT_FOUND, "User")
        return UserResponse.model_validate(user)
    
    async def get_by_email(self, email: str) -> UserResponse:
        """Get user by email."""
        user = await self.repository.get_by_email(email)
        if not user:
            raise NotFoundException(Messages.USER_NOT_FOUND, "User")
        return UserResponse.model_validate(user)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination."""
        users = await self.repository.find_all(skip, limit)
        return [UserResponse.model_validate(u) for u in users]


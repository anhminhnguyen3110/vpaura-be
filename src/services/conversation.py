"""Conversation service for managing user conversations."""

from ..repositories.conversation import ConversationRepository
from ..schemas.conversation import ConversationCreate, ConversationResponse
from ..models.conversation import Conversation
from ..exceptions.base import NotFoundException
from ..constants.messages import Messages
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation-related operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = ConversationRepository(session)
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation."""
        conversation = Conversation(
            title=conversation_data.title,
            user_id=conversation_data.user_id,
            extra_data=conversation_data.extra_data
        )
        
        created = await self.repository.create(conversation)
        return ConversationResponse.model_validate(created)
    
    async def get_by_id(self, conversation_id: int) -> ConversationResponse:
        """Get a conversation by ID."""
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise NotFoundException(Messages.CONVERSATION_NOT_FOUND, "Conversation")
        return ConversationResponse.model_validate(conversation)
    
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ConversationResponse]:
        """Get all conversations for a user."""
        conversations = await self.repository.get_by_user_id(user_id, skip, limit)
        return [ConversationResponse.model_validate(c) for c in conversations]
    
    async def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        return await self.repository.delete(conversation_id)


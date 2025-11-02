"""Message service for managing session messages."""

from ..repositories.message import MessageRepository
from ..schemas.message import MessageCreate, MessageResponse
from ..models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message-related operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = MessageRepository(session)
    
    async def create_message(self, message_data: MessageCreate) -> MessageResponse:
        """Create a new message."""
        message = Message(
            content=message_data.content,
            role=message_data.role,
            session_id=message_data.session_id,
            extra_data=message_data.extra_data
        )
        
        created = await self.repository.create(message)
        return MessageResponse.model_validate(created)
    
    async def get_by_session(self, session_id: int, limit: int = 20) -> List[MessageResponse]:
        """Get messages for a session."""
        messages = await self.repository.get_by_session_id(session_id, limit=limit)
        return [MessageResponse.model_validate(m) for m in messages]
    
    async def delete_message(self, message_id: int) -> bool:
        """Delete a message."""
        return await self.repository.delete(message_id)


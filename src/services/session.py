"""Session service for managing user sessions."""

from ..repositories.session import SessionRepository
from ..schemas.session import SessionCreate, SessionResponse, SessionUpdate
from ..models.session import Session
from ..exceptions.base import NotFoundException
from ..constants.messages import Messages
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """Service for session-related operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = SessionRepository(session)
    
    async def create_session(self, session_data: SessionCreate) -> SessionResponse:
        """Create a new session."""
        session_obj = Session(
            name=session_data.name,
            user_id=session_data.user_id,
            extra_data=session_data.extra_data
        )
        
        created = await self.repository.create(session_obj)
        return SessionResponse.model_validate(created)
    
    async def get_by_id(self, session_id: int) -> SessionResponse:
        """Get a session by ID."""
        session_obj = await self.repository.get_by_id(session_id)
        if not session_obj:
            raise NotFoundException(Messages.SESSION_NOT_FOUND, "Session")
        return SessionResponse.model_validate(session_obj)
    
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[SessionResponse]:
        """Get all sessions for a user."""
        sessions = await self.repository.get_by_user_id(user_id, skip, limit)
        return [SessionResponse.model_validate(s) for s in sessions]
    
    async def update_session(self, session_id: int, session_data: SessionUpdate) -> SessionResponse:
        """Update a session."""
        session_obj = await self.repository.get_by_id(session_id)
        if not session_obj:
            raise NotFoundException(Messages.SESSION_NOT_FOUND, "Session")
        
        # Update fields
        if session_data.name is not None:
            session_obj.name = session_data.name
        if session_data.extra_data is not None:
            session_obj.extra_data = session_data.extra_data
        
        updated = await self.repository.update(session_obj)
        return SessionResponse.model_validate(updated)
    
    async def delete_session(self, session_id: int) -> bool:
        """Delete a session and its checkpoints."""
        try:
            from ..ai_core.agents.agent_factory import AgentFactory, AgentType
            agent = AgentFactory.create(AgentType.CHAT)
            await agent.clear_session_history(str(session_id))
            logger.info(f"Cleared checkpoints for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to clear checkpoints for session {session_id}: {e}")
        
        return await self.repository.delete(session_id)

"""Chatbot service for smart chat with agent routing and DB persistence."""

from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..ai_core.agents import AgentRouter
from ..ai_core.agents.agent_factory import AgentFactory, AgentType
from ..schemas.chatbot import ChatRequest, ChatResponse, ChatCompletionRequest, ChatCompletionResponse, StreamChunk
from ..schemas.message import MessageCreate
from ..schemas.session import SessionCreate
from ..repositories.session import SessionRepository
from ..repositories.message import MessageRepository
from .message import MessageService
from .session import SessionService
from .chat_completion import ChatCompletionService
from ..models.session import Session
from ..models.message import Message
from ..constants.enums import MessageRole
from ..exceptions.service import LLMException

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Unified chatbot service with agent intelligence and DB persistence.
    
    Features:
    - chat(): Smart chat with auto intent detection + DB save
    - chat_stream(): Streaming chat with auto detect + DB save
    - completion(): Raw LLM completion (no agent, no DB)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.router = AgentRouter()
        self.session_repo = SessionRepository(session)
        self.message_repo = MessageRepository(session)
        self.session_service = SessionService(session)
        self.message_service = MessageService(session)
        self.completion_service = ChatCompletionService()
    
    async def chat(
        self,
        request: ChatRequest,
        user_id: int,
        confidence_threshold: float = 0.6
    ) -> ChatResponse:
        """
        Smart chat with automatic intent detection and DB persistence.
        
        Args:
            request: Chat request with query and optional history
            user_id: User ID for conversation tracking
            confidence_threshold: Minimum confidence for auto-routing
            
        Returns:
            ChatResponse with agent-generated response
        """
        logger.info(f"Chat request from user {user_id}: {request.query[:50]}...")
        
        try:
            session_obj = await self._get_or_create_session(
                request.session_id,
                user_id,
                request.query
            )
            
            await self._save_user_message(session_obj.id, request.query)
            
            history = await self._build_history(session_obj.id, request.history)
            
            result = await self.router.route(
                user_input=request.query,
                session_id=str(session_obj.id),
                user_id=user_id,
                agent_type=None,
                config={"history": history} if history else None,
                confidence_threshold=confidence_threshold
            )
            
            routing = result.get("_routing", {})
            agent_type = routing.get("agent_type")
            confidence = routing.get("confidence")
            
            response_text = result.get("response", "")
            
            await self._save_assistant_message(
                session_obj.id,
                response_text,
                extra_data={
                    "agent_type": agent_type,
                    "confidence": confidence
                }
            )
            
            return ChatResponse(
                query=request.query,
                response=response_text,
                agent_type=agent_type,
                confidence=confidence,
                session_id=str(session_obj.id),
                error=result.get("error")
            )
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}", exc_info=True)
            return ChatResponse(
                query=request.query,
                response="I apologize, but I encountered an error processing your request.",
                error=str(e)
            )
    
    async def chat_stream(
        self,
        request: ChatRequest,
        user_id: int,
        confidence_threshold: float = 0.6
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        REAL streaming chat with automatic intent detection and DB persistence.
        
        Args:
            request: Chat request with query and optional history
            user_id: User ID for conversation tracking
            confidence_threshold: Minimum confidence for auto-routing
            
        Yields:
            StreamChunk dict with type: "chunk" | "error" | "done"
        """
        logger.info(f"Stream chat request from user {user_id}: {request.query[:50]}...")
        
        try:
            session_obj = await self._get_or_create_session(
                request.session_id,
                user_id,
                request.query
            )
            
            await self._save_user_message(session_obj.id, request.query)
            
            history = await self._build_history(session_obj.id, request.history)
            
            # Detect intent (with confidence-based fallback)
            auto_routed = False
            confidence = 1.0
            agent_type_enum = None
            
            detected_type, confidence = await self.router.detect_intent(request.query)
            
            if confidence < confidence_threshold:
                logger.warning(
                    f"Low confidence ({confidence:.2f}) for {detected_type}, "
                    f"defaulting to CHAT agent"
                )
                agent_type_enum = AgentType.CHAT
            else:
                agent_type_enum = detected_type
                auto_routed = True
                logger.info(f"Auto-routed to {agent_type_enum} (confidence: {confidence:.2f})")
            
            # Create agent directly (bypass router to use execute_stream)
            agent = AgentFactory.create(agent_type_enum, config=None)
            
            full_response = ""
            async for token in agent.execute_stream(
                query=request.query,
                session_id=str(session_obj.id),
                user_id=user_id,
                history=history,
                system_prompt=None,
                metadata={
                    "session_id": str(session_obj.id),
                    "agent_type": agent_type_enum.value,
                    "auto_routed": auto_routed,
                    "confidence": confidence
                }
            ):
                full_response += token
                yield StreamChunk(
                    type="chunk",
                    content=token,
                    metadata={"agent_type": agent_type_enum.value}
                ).model_dump()
            
            await self._save_assistant_message(
                session_obj.id,
                full_response,
                extra_data={
                    "agent_type": agent_type_enum.value,
                    "confidence": confidence,
                    "auto_routed": auto_routed
                }
            )
            
            yield StreamChunk(
                type="done",
                content="",
                metadata={
                    "session_id": str(session_obj.id),
                    "agent_type": agent_type_enum.value,
                    "confidence": confidence
                }
            ).model_dump()
                
        except Exception as e:
            logger.error(f"Stream chat failed: {str(e)}", exc_info=True)
            yield StreamChunk(
                type="error",
                content=str(e),
                metadata={"error_type": type(e).__name__}
            ).model_dump()
    
    async def completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Raw LLM completion without agent routing or DB persistence."""
        logger.info(f"Completion request: {request.prompt[:50]}...")
        return await self.completion_service.complete(request)
    
    async def _get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: int,
        query: str
    ) -> Session:
        """Get existing session or create new one."""
        if session_id:
            try:
                session_int = int(session_id)
                session_obj = await self.session_repo.get_by_id(session_int)
                if session_obj:
                    return session_obj
            except (ValueError, TypeError):
                logger.warning(f"Invalid session_id format: {session_id}")
        
        session_obj = Session(
            name=query[:50],
            user_id=user_id,
            extra_data={}
        )
        return await self.session_repo.create(session_obj)
    
    async def _save_user_message(self, session_id: int, content: str) -> Message:
        """Save user message to DB."""
        message = Message(
            content=content,
            role=MessageRole.USER,
            session_id=session_id,
            extra_data={}
        )
        return await self.message_repo.create(message)
    
    async def _save_assistant_message(
        self,
        session_id: int,
        content: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Save assistant message to DB."""
        message = Message(
            content=content,
            role=MessageRole.ASSISTANT,
            session_id=session_id,
            extra_data=extra_data or {}
        )
        return await self.message_repo.create(message)
    
    async def _build_history(
        self,
        session_id: int,
        provided_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build conversation history from DB or use provided history."""
        if provided_history:
            return provided_history
        
        messages = await self.message_repo.get_by_session_id(
            session_id,
            limit=20
        )
        
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]


"""Chatbot service for smart chat with agent routing and DB persistence."""

from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..ai_core.agents import AgentRouter
from ..schemas.chatbot import ChatRequest, ChatResponse, ChatCompletionRequest, ChatCompletionResponse
from ..schemas.message import MessageCreate
from ..schemas.conversation import ConversationCreate
from ..repositories.conversation import ConversationRepository
from ..repositories.message import MessageRepository
from .message import MessageService
from .conversation import ConversationService
from .chat_completion import ChatCompletionService
from ..models.conversation import Conversation
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
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.conversation_service = ConversationService(session)
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
            conversation = await self._get_or_create_conversation(
                request.conversation_id,
                user_id,
                request.query
            )
            
            await self._save_user_message(conversation.id, request.query)
            
            history = await self._build_history(conversation.id, request.history)
            
            # Route to appropriate agent with history in config
            result = await self.router.route(
                user_input=request.query,
                agent_type=None,  # Auto-detect
                config={"history": history} if history else None,
                confidence_threshold=confidence_threshold
            )
            
            # Extract routing metadata
            routing = result.get("_routing", {})
            agent_type = routing.get("agent_type")
            confidence = routing.get("confidence")
            
            response_text = result.get("response", "")
            
            await self._save_assistant_message(
                conversation.id,
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
                conversation_id=conversation.id,
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
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat with automatic intent detection and DB persistence.
        
        Args:
            request: Chat request with query and optional history
            user_id: User ID for conversation tracking
            confidence_threshold: Minimum confidence for auto-routing
            
        Yields:
            Response chunks
        """
        logger.info(f"Stream chat request from user {user_id}: {request.query[:50]}...")
        
        try:
            conversation = await self._get_or_create_conversation(
                request.conversation_id,
                user_id,
                request.query
            )
            
            await self._save_user_message(conversation.id, request.query)
            
            history = await self._build_history(conversation.id, request.history)
            
            # Route to appropriate agent with history in config
            result = await self.router.route(
                user_input=request.query,
                agent_type=None,  # Auto-detect
                config={"history": history} if history else None,
                confidence_threshold=confidence_threshold
            )
            
            # Extract routing metadata
            routing = result.get("_routing", {})
            agent_type = routing.get("agent_type")
            confidence = routing.get("confidence")
            
            response_text = result.get("response", "")
            
            await self._save_assistant_message(
                conversation.id,
                response_text,
                extra_data={
                    "agent_type": agent_type,
                    "confidence": confidence
                }
            )
            
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                yield response_text[i:i + chunk_size]
                
        except Exception as e:
            logger.error(f"Stream chat failed: {str(e)}", exc_info=True)
            yield f"[ERROR] {str(e)}"
    
    async def completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Raw LLM completion without agent routing or DB persistence."""
        logger.info(f"Completion request: {request.prompt[:50]}...")
        return await self.completion_service.complete(request)
    
    async def _get_or_create_conversation(
        self,
        conversation_id: Optional[int],
        user_id: int,
        query: str
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            conversation = await self.conversation_repo.get_by_id(conversation_id)
            if conversation:
                return conversation
        
        conversation = Conversation(
            title=query[:50],
            user_id=user_id,
            extra_data={}
        )
        return await self.conversation_repo.create(conversation)
    
    async def _save_user_message(self, conversation_id: int, content: str) -> Message:
        """Save user message to DB."""
        message = Message(
            content=content,
            role=MessageRole.USER,
            conversation_id=conversation_id,
            extra_data={}
        )
        return await self.message_repo.create(message)
    
    async def _save_assistant_message(
        self,
        conversation_id: int,
        content: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Save assistant message to DB."""
        message = Message(
            content=content,
            role=MessageRole.ASSISTANT,
            conversation_id=conversation_id,
            extra_data=extra_data or {}
        )
        return await self.message_repo.create(message)
    
    async def _build_history(
        self,
        conversation_id: int,
        provided_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build conversation history from DB or use provided history."""
        if provided_history:
            return provided_history
        
        messages = await self.message_repo.get_by_conversation_id(
            conversation_id,
            limit=20
        )
        
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]


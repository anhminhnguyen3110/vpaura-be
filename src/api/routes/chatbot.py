"""Chatbot API routes with unified agent-powered chat."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ...schemas.chatbot import ChatRequest, ChatResponse, ChatCompletionRequest, ChatCompletionResponse
from ...services.chatbot import ChatbotService
from ...core.streaming import StreamingResponse as SSEStreaming
from ...database.session import get_db_session

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: int = Query(..., description="User ID for conversation tracking"),
    confidence_threshold: float = Query(0.6, description="Minimum confidence for auto-routing"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Smart chat with automatic intent detection and DB persistence.
    
    Auto-routes to appropriate agent (Chat, Neo4j, RAG) based on query intent.
    Saves conversation and messages to database.
    """
    service = ChatbotService(session)
    return await service.chat(
        request=request,
        user_id=user_id,
        confidence_threshold=confidence_threshold
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user_id: int = Query(..., description="User ID for conversation tracking"),
    confidence_threshold: float = Query(0.6, description="Minimum confidence for auto-routing"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Streaming smart chat with automatic intent detection and DB persistence.
    
    Auto-routes to appropriate agent and streams response in chunks.
    Saves conversation and messages to database.
    """
    service = ChatbotService(session)
    
    async def event_stream():
        async for chunk in SSEStreaming.stream_generator(
            service.chat_stream(
                request=request,
                user_id=user_id,
                confidence_threshold=confidence_threshold
            )
        ):
            yield chunk
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )


@router.post("/completion", response_model=ChatCompletionResponse)
async def completion(request: ChatCompletionRequest):
    """
    Raw LLM completion without agent routing or DB persistence.
    
    Direct LLM call with optional guardrail validation.
    No agent intelligence, no conversation history, no database save.
    """
    service = ChatbotService(None)  # No session needed for completion
    return await service.completion(request)


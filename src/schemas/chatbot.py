from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Literal
from ..constants.enums import MessageRole


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class StreamChunk(BaseModel):
    """Streaming response chunk with type."""
    type: Literal["chunk", "error", "done"]
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request for smart chat with agent routing."""
    query: str
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response from smart chat."""
    query: str
    response: str
    agent_type: Optional[str] = None
    confidence: Optional[float] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    use_guardrail: Optional[bool] = True


class ChatCompletionResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    guardrail_result: Optional[Dict[str, Any]] = None


class DeleteMessagesRequest(BaseModel):
    session_id: str
    message_ids: Optional[List[int]] = None


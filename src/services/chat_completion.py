"""Chat completion service for raw LLM interactions."""

from ..schemas.chatbot import ChatCompletionRequest, ChatCompletionResponse
from ..config.settings import settings
from langchain_core.messages import HumanMessage
from ..exceptions.service import LLMException
from ..ai_core.llm import LLMFactory, LLMProviderType
import logging

logger = logging.getLogger(__name__)


class ChatCompletionService:
    """Service for raw chat completions (no agents, no DB persistence)."""
    
    def __init__(self):
        self.llm = LLMFactory.create(
            provider_type=LLMProviderType(settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
            enable_guardrail=settings.ENABLE_GUARDRAIL
        )
    
    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Execute a chat completion with optional guardrail."""
        try:
            # Create LLM with custom parameters if provided
            llm = LLMFactory.create(
                provider_type=LLMProviderType(settings.LLM_PROVIDER),
                model=request.model or settings.LLM_MODEL,
                temperature=request.temperature or settings.LLM_TEMPERATURE,
                max_tokens=request.max_tokens or settings.LLM_MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY,
                enable_guardrail=request.use_guardrail if request.use_guardrail is not None else settings.ENABLE_GUARDRAIL
            )
            
            # Guardrail validation happens automatically in ainvoke
            try:
                response = await llm.ainvoke([HumanMessage(content=request.prompt)])
            except ValueError as ve:
                # Guardrail blocked the request/response
                return ChatCompletionResponse(
                    content=str(ve),
                    model=request.model or settings.LLM_MODEL,
                    guardrail_result={"valid": False, "reason": str(ve), "blocked": True}
                )
            
            return ChatCompletionResponse(
                content=response.content,
                model=request.model or settings.LLM_MODEL,
                usage={
                    "prompt_tokens": response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response.response_metadata.get("token_usage", {}).get("completion_tokens", 0),
                    "total_tokens": response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
                },
                guardrail_result={"valid": True, "reason": None, "blocked": False}
            )
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise LLMException(f"Chat completion failed: {str(e)}")


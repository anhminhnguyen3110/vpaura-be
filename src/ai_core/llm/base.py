"""Base LLM Provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, AIMessage
from ..guardrail.manager import GuardrailManager
from ...config.settings import settings, Environment
from ...core.logger import logger
from ...middleware.metrics import llm_request_count, llm_inference_duration_seconds

base_logger = logger.bind(module="llm_provider")


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with integrated guardrails."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_guardrail: bool = True,
        fallback_model: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ):
        """Initialize the LLM provider."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_guardrail = enable_guardrail
        self.fallback_model = fallback_model
        self.max_retries = max_retries
        self.kwargs = kwargs
        self._client = None
        self._guardrail_manager = GuardrailManager() if enable_guardrail else None
        self._environment = settings.ENVIRONMENT
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the LLM client."""
        pass
    
    @property
    def client(self) -> Any:
        """Get the LLM client, initializing if necessary."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    @abstractmethod
    async def _ainvoke_internal(self, messages: List[BaseMessage]) -> Any:
        """Internal async invoke method to be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _invoke_internal(self, messages: List[BaseMessage]) -> Any:
        """Internal sync invoke method to be implemented by subclasses."""
        pass
    
    async def _validate_input(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Validate input messages using guardrails."""
        if not self._guardrail_manager:
            return {"valid": True, "reason": None, "blocked": False}
        
        combined_text = " ".join([msg.content for msg in messages if hasattr(msg, 'content')])
        return await self._guardrail_manager.validate_input(combined_text)
    
    async def _validate_output(self, response_text: str) -> Dict[str, Any]:
        """Validate output response using guardrails."""
        if not self._guardrail_manager:
            return {"valid": True, "reason": None, "blocked": False}
        
        return await self._guardrail_manager.validate_output(response_text)
    
    async def ainvoke(self, messages: List[BaseMessage]) -> Any:
        """Asynchronously invoke the LLM with messages (with guardrails + retry + fallback)."""
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Guardrail validation
                input_validation = await self._validate_input(messages)
                if not input_validation["valid"]:
                    raise ValueError(f"Input blocked by guardrail: {input_validation['reason']}")
                
                # Metrics tracking
                with llm_inference_duration_seconds.labels(
                    model=self.model,
                    environment=self._environment.value
                ).time():
                    response = await self._ainvoke_internal(messages)
                
                # Output validation
                response_text = response.content if hasattr(response, 'content') else str(response)
                output_validation = await self._validate_output(response_text)
                if not output_validation["valid"]:
                    raise ValueError(f"Output blocked by guardrail: {output_validation['reason']}")
                
                # Track success
                llm_request_count.labels(
                    model=self.model,
                    status="success"
                ).inc()
                
                return response
                
            except Exception as e:
                base_logger.error(
                    "llm_call_failed",
                    model=self.model,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                
                # Fallback strategy (production only)
                if (self._environment == Environment.PRODUCTION 
                    and self.fallback_model 
                    and attempt == self.max_retries - 2):
                    base_logger.warning(
                        "switching_to_fallback_model",
                        from_model=self.model,
                        to_model=self.fallback_model
                    )
                    self.model = self.fallback_model
                    self._client = None  # Force reinit
                    continue
                
                # Last attempt
                if attempt == self.max_retries - 1:
                    llm_request_count.labels(
                        model=self.model,
                        status="error"
                    ).inc()
                    
                    # Production degradation
                    if self._environment == Environment.PRODUCTION:
                        base_logger.error("llm_all_retries_failed_degrading")
                        return self._get_fallback_response(e)
                    raise
        
        raise RuntimeError(f"Failed after {self.max_retries} attempts")
    
    def invoke(self, messages: List[BaseMessage]) -> Any:
        """Synchronously invoke the LLM (guardrails work only with ainvoke)."""
        return self._invoke_internal(messages)
    
    def _get_fallback_response(self, error: Exception) -> AIMessage:
        """Production fallback response when all retries fail."""
        base_logger.error(
            "returning_fallback_response",
            error=str(error),
            error_type=type(error).__name__
        )
        return AIMessage(
            content="I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        )
    
    def _get_environment_model_kwargs(self) -> Dict[str, Any]:
        """Get environment-specific model parameters."""
        base_kwargs = {}
        
        if self._environment == Environment.DEVELOPMENT:
            # Dev: Fast & cheap
            base_kwargs.update({
                "top_p": 0.8,
                "timeout": 30,
            })
        elif self._environment == Environment.PRODUCTION:
            # Prod: High quality & reliable
            base_kwargs.update({
                "top_p": 0.95,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1,
                "timeout": 60,
            })
        
        return base_kwargs
    
    def update_config(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> None:
        """Update provider configuration."""
        if model is not None:
            self.model = model
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if kwargs:
            self.kwargs.update(kwargs)
        
        self._client = None
    
    def get_config(self) -> Dict[str, Any]:
        """Get current provider configuration."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **self.kwargs
        }

"""Base LLM Provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage
from ..guardrail.manager import GuardrailManager


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with integrated guardrails."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_guardrail: bool = True,
        **kwargs
    ):
        """Initialize the LLM provider."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_guardrail = enable_guardrail
        self.kwargs = kwargs
        self._client = None
        self._guardrail_manager = GuardrailManager() if enable_guardrail else None
    
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
        """Asynchronously invoke the LLM with messages (with guardrails)."""
        input_validation = await self._validate_input(messages)
        if not input_validation["valid"]:
            raise ValueError(f"Input blocked by guardrail: {input_validation['reason']}")
        
        response = await self._ainvoke_internal(messages)
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        output_validation = await self._validate_output(response_text)
        if not output_validation["valid"]:
            raise ValueError(f"Output blocked by guardrail: {output_validation['reason']}")
        
        return response
    
    def invoke(self, messages: List[BaseMessage]) -> Any:
        """Synchronously invoke the LLM (guardrails work only with ainvoke)."""
        return self._invoke_internal(messages)
    
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

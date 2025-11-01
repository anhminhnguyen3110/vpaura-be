"""OpenAI LLM Provider implementation."""

from typing import Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using langchain_openai."""
    
    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: str = None,
        base_url: str = None,
        enable_guardrail: bool = True,
        **kwargs
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name (e.g., gpt-4, gpt-3.5-turbo)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            api_key: OpenAI API key
            base_url: Base URL for API (for OpenAI-compatible endpoints like OpenRouter)
            enable_guardrail: Enable guardrail validation
            **kwargs: Additional ChatOpenAI parameters
        """
        super().__init__(model, temperature, max_tokens, enable_guardrail, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
    
    def _initialize_client(self) -> ChatOpenAI:
        """
        Initialize the ChatOpenAI client.
        
        Returns:
            Initialized ChatOpenAI instance
        """
        config = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        if self.api_key:
            config["api_key"] = self.api_key
        
        if self.base_url:
            config["base_url"] = self.base_url
        
        # Add any additional kwargs
        config.update(self.kwargs)
        
        return ChatOpenAI(**config)
    
    async def _ainvoke_internal(self, messages: List[BaseMessage]) -> Any:
        """
        Internal async invoke implementation for OpenAI.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AI response message
        """
        return await self.client.ainvoke(messages)
    
    def _invoke_internal(self, messages: List[BaseMessage]) -> Any:
        """
        Internal sync invoke implementation for OpenAI.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AI response message
        """
        return self.client.invoke(messages)

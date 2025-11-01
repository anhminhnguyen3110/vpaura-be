"""LLM Factory for creating LLM provider instances."""

from typing import Dict, Type, Optional
from enum import Enum

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .bedrock_provider import BedrockProvider


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    BEDROCK = "bedrock"


class LLMFactory:
    """Factory class for creating LLM provider instances."""
    
    # Registry of available providers
    _providers: Dict[LLMProviderType, Type[BaseLLMProvider]] = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.BEDROCK: BedrockProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_type: LLMProviderType = LLMProviderType.OPENAI,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider to create
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Initialized LLM provider instance
            
        Raises:
            ValueError: If provider_type is not supported
            
        Examples:
            >>> # Create OpenAI provider
            >>> llm = LLMFactory.create(
            ...     provider_type=LLMProviderType.OPENAI,
            ...     model="gpt-4",
            ...     api_key="sk-..."
            ... )
            
            >>> # Create Bedrock provider (when implemented)
            >>> llm = LLMFactory.create(
            ...     provider_type=LLMProviderType.BEDROCK,
            ...     model="anthropic.claude-v2",
            ...     region_name="us-east-1"
            ... )
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_type]
        
        # Build kwargs for provider initialization
        init_kwargs = {}
        if model is not None:
            init_kwargs["model"] = model
        if temperature is not None:
            init_kwargs["temperature"] = temperature
        if max_tokens is not None:
            init_kwargs["max_tokens"] = max_tokens
        
        # Add any additional kwargs
        init_kwargs.update(kwargs)
        
        return provider_class(**init_kwargs)
    
    @classmethod
    def register_provider(
        cls,
        provider_type: LLMProviderType,
        provider_class: Type[BaseLLMProvider]
    ) -> None:
        """
        Register a new LLM provider type.
        
        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class to register
            
        Raises:
            TypeError: If provider_class is not a BaseLLMProvider subclass
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise TypeError(
                f"Provider class must be a subclass of BaseLLMProvider, "
                f"got {provider_class}"
            )
        
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> list[LLMProviderType]:
        """
        Get list of available provider types.
        
        Returns:
            List of available provider types
        """
        return list(cls._providers.keys())

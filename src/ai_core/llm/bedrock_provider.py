"""AWS Bedrock LLM Provider (placeholder)."""

from typing import Any, List
from langchain_core.messages import BaseMessage

from .base import BaseLLMProvider


class BedrockProvider(BaseLLMProvider):
    """
    AWS Bedrock LLM provider using langchain_aws.
    
    Note: Currently not in use. Placeholder for future implementation.
    To use, install: pip install langchain-aws boto3
    """
    
    def __init__(
        self,
        model: str = "anthropic.claude-v2",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        region_name: str = "us-east-1",
        enable_guardrail: bool = True,
        **kwargs
    ):
        """
        Initialize Bedrock provider.
        
        Args:
            model: Bedrock model ID (e.g., anthropic.claude-v2)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            region_name: AWS region name
            enable_guardrail: Enable guardrail validation
            **kwargs: Additional Bedrock parameters
        """
        super().__init__(model, temperature, max_tokens, enable_guardrail, **kwargs)
        self.region_name = region_name
    
    def _initialize_client(self) -> Any:
        """
        Initialize the Bedrock client.
        
        Returns:
            Initialized Bedrock instance
            
        Raises:
            NotImplementedError: This provider is not yet implemented
        """
        raise NotImplementedError(
            "BedrockProvider is not yet implemented. "
            "Install langchain-aws and boto3 to use this provider."
        )
    
    async def _ainvoke_internal(self, messages: List[BaseMessage]) -> Any:
        """
        Internal async invoke implementation for Bedrock.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AI response message
            
        Raises:
            NotImplementedError: This provider is not yet implemented
        """
        raise NotImplementedError("BedrockProvider is not yet implemented")
    
    def _invoke_internal(self, messages: List[BaseMessage]) -> Any:
        """
        Internal sync invoke implementation for Bedrock.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AI response message
            
        Raises:
            NotImplementedError: This provider is not yet implemented
        """
        raise NotImplementedError("BedrockProvider is not yet implemented")

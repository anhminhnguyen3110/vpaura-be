"""Base tool interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools are discrete functions that agents can use
    for reasoning, planning, or execution.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name identifier.
        
        Returns:
            Tool name string
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description for LLM understanding.
        
        Returns:
            Description string
        """
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass

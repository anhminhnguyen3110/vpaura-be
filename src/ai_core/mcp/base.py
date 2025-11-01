"""Base MCP client interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseMCPClient(ABC):
    """
    Abstract base class for MCP (Model Context Protocol) clients.
    
    MCP provides a standardized way to interact with external services
    like databases, APIs, etc.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP client.
        
        Args:
            config: Client configuration
        """
        self.config = config or {}
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to MCP server.
        
        Should handle connection pooling and error handling.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to MCP server.
        
        Should clean up resources properly.
        """
        pass
    
    @abstractmethod
    async def execute(self, command: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute MCP command.
        
        Args:
            command: Command to execute
            params: Command parameters
            
        Returns:
            Command execution result
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connection is not None

"""Agent factory with registry pattern."""

from typing import Dict, Type, Optional, Any
from enum import Enum
from .base.base import BaseAgent
from .chat_agent.agent import ChatAgent
from .neo4j_agent.agent import Neo4jAgent
from .rag_agent.agent import RAGAgent


class AgentType(str, Enum):
    """Available agent types."""
    NEO4J = "neo4j"
    RAG = "rag"
    CHAT = "chat"


class AgentFactory:
    """
    Factory for creating agent instances.
    
    Uses registry pattern for extensibility.
    """
    
    # Registry mapping agent types to classes
    _agents: Dict[AgentType, Type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, agent_type: AgentType, agent_class: Type[BaseAgent]) -> None:
        """
        Register a new agent type.
        
        Args:
            agent_type: Type identifier
            agent_class: Agent class to register
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(
                f"Agent class must be a subclass of BaseAgent, got {agent_class}"
            )
        
        cls._agents[agent_type] = agent_class
    
    @classmethod
    def create(
        cls, 
        agent_type: AgentType, 
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """
        Create agent instance.
        
        Args:
            agent_type: Type of agent to create
            config: Optional configuration dict
            
        Returns:
            Initialized agent instance
            
        Raises:
            ValueError: If agent type not registered
        """
        if agent_type not in cls._agents:
            available = ", ".join([t.value for t in cls._agents.keys()])
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available agents: {available}"
            )
        
        agent_class = cls._agents[agent_type]
        return agent_class(config)
    
    @classmethod
    def get_available_agents(cls) -> list[AgentType]:
        """
        Get list of registered agent types.
        
        Returns:
            List of available agent types
        """
        return list(cls._agents.keys())


def _register_builtin_agents():
    """Register default agent implementations."""
    AgentFactory.register(AgentType.CHAT, ChatAgent)
    AgentFactory.register(AgentType.NEO4J, Neo4jAgent)
    AgentFactory.register(AgentType.RAG, RAGAgent)


_register_builtin_agents()


"""Base agent class with logging and metrics tracking."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time

from ....core.logger import logger as base_logger
from ....middleware.metrics import (
    agent_invocations_total,
    agent_response_time_seconds,
)

from .state import BaseAgentState
from ....config.settings import settings


class BaseAgent(ABC):
    """Abstract base class for all agents with LangGraph support."""
    
    MAX_HISTORY_MESSAGES = 10
    MAX_CONTEXT_TOKENS = 4000
    
    def __init__(
        self, 
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize agent."""
        self.agent_type = agent_type
        self.config = config or {}
        self.logger = base_logger.bind(agent_type=agent_type)
        
        self.enable_langfuse = self.config.get("enable_langfuse", settings.LANGFUSE_ENABLED)
        self._langfuse_handler = None
        self._graph_config = None
        
        self.graph = self._build_graph()
        
        self._graph_config = self._build_graph_config()
        
        self.max_history = self.config.get("max_history", self.MAX_HISTORY_MESSAGES)
        self.max_tokens = self.config.get("max_context_tokens", self.MAX_CONTEXT_TOKENS)
    
    def _build_graph_config(self) -> Optional[Dict[str, Any]]:
        """Build graph configuration with optional Langfuse callbacks."""
        config = {
            "recursion_limit": 100
        }
        
        if not self.enable_langfuse:
            return config
        
        try:
            from langfuse.langchain import CallbackHandler
            
            if self._langfuse_handler is None:
                self._langfuse_handler = CallbackHandler()
                self.logger.info(
                    f"Langfuse tracing initialized for {self.agent_type} agent"
                )
            
            config["callbacks"] = [self._langfuse_handler]
            return config
            
        except ImportError:
            self.logger.warning(
                f"Langfuse enabled but not installed for {self.agent_type}. "
                "Install with: pip install langfuse"
            )
            return config
    
    @property
    def graph_config(self) -> Optional[Dict[str, Any]]:
        """Get graph configuration for LangGraph execution."""
        return self._graph_config
    
    @property
    def langfuse_config(self) -> Optional[Dict[str, Any]]:
        """Deprecated: Use graph_config instead."""
        return self._graph_config
    
    @abstractmethod
    def _build_graph(self):
        """Build and compile LangGraph for this agent."""
        pass
    
    def truncate_history(
        self,
        history: List[Dict[str, str]],
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """Truncate conversation history to fit within context window.
        
        Strategy: Keep system message, most recent messages up to max_history,
        and estimate tokens to truncate further if needed.
        """
        if not history:
            return []
        
        truncated = []
        
        system_msg = None
        if include_system and history and history[0].get("role") == "system":
            system_msg = history[0]
            history = history[1:]
        
        max_messages = self.max_history * 2
        recent_history = history[-max_messages:] if len(history) > max_messages else history
        
        estimated_tokens = 0
        if system_msg:
            estimated_tokens += len(str(system_msg.get("content", ""))) // 4
        
        for msg in reversed(recent_history):
            msg_tokens = len(str(msg.get("content", ""))) // 4
            
            if estimated_tokens + msg_tokens > self.max_tokens:
                self.logger.info(
                    "history_truncated_by_tokens",
                    total_messages=len(history),
                    kept_messages=len(truncated),
                    estimated_tokens=estimated_tokens
                )
                break
            
            truncated.insert(0, msg)
            estimated_tokens += msg_tokens
        
        if system_msg:
            truncated.insert(0, system_msg)
        
        if len(truncated) < len(history):
            self.logger.info(
                "history_truncated",
                original_count=len(history),
                truncated_count=len(truncated),
                max_history=self.max_history
            )
        
        return truncated
    
    async def execute(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute agent with full tracking and memory management."""
        truncated_history = self.truncate_history(history or [])
        
        state: BaseAgentState = {
            "query": query,
            "history": truncated_history,
            "metadata": metadata or {},
        }
        
        return await self._execute_internal(state)
    
    async def _execute_internal(self, state: BaseAgentState) -> Dict[str, Any]:
        """Internal execution with tracking and optional Langfuse tracing."""
        self.logger.info(
            "agent_execution_started",
            agent_type=self.agent_type,
            query_length=len(state.get("query", "")),
            history_length=len(state.get("history", [])),
            langfuse_enabled=self.enable_langfuse,
            has_config=self.graph_config is not None
        )
        
        start_time = time.time()
        
        try:
            result = await self.graph.ainvoke(state, config=self.graph_config)
            
            duration = time.time() - start_time
            
            self.logger.info(
                "agent_execution_completed",
                agent_type=self.agent_type,
                duration_ms=int(duration * 1000),
                status="success"
            )
            
            agent_invocations_total.labels(
                agent_type=self.agent_type,
                status="success"
            ).inc()
            
            agent_response_time_seconds.labels(
                agent_type=self.agent_type
            ).observe(duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            self.logger.error(
                "agent_execution_failed",
                agent_type=self.agent_type,
                duration_ms=int(duration * 1000),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            agent_invocations_total.labels(
                agent_type=self.agent_type,
                status="error"
            ).inc()
            
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config

"""Base agent class with logging and metrics tracking."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
import logging

# Import metrics from middleware
from ...middleware.metrics import (
    agent_invocations_total,
    agent_response_time_seconds,
)

from .state.chat_state import ChatState
from ...config.settings import settings


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides:
    - LangGraph building
    - Execution with logging
    - Metrics tracking (Prometheus)
    - Error handling
    - Optional LangFuse tracing
    - Conversation memory with truncation
    """
    
    # Memory configuration
    MAX_HISTORY_MESSAGES = 10  # Max number of message pairs to keep
    MAX_CONTEXT_TOKENS = 4000  # Approximate token limit for context
    
    def __init__(
        self, 
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent.
        
        Args:
            agent_type: Type identifier for the agent
            config: Optional configuration dict with:
                - enable_langfuse: bool (default: from settings.ENABLE_LANGFUSE)
                - max_history: int (default: MAX_HISTORY_MESSAGES)
                - max_context_tokens: int (default: MAX_CONTEXT_TOKENS)
        """
        self.agent_type = agent_type
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_type}")
        
        # Langfuse configuration
        self.enable_langfuse = self.config.get("enable_langfuse", settings.LANGFUSE_ENABLED)
        self._langfuse_handler = None
        self._graph_config = None  # Will be set after initialization
        
        # Build graph (will use langfuse config if enabled)
        self.graph = self._build_graph()
        
        # Setup graph config (always set, even if None)
        self._graph_config = self._build_graph_config()
        
        # Memory settings (can be overridden in config)
        self.max_history = self.config.get("max_history", self.MAX_HISTORY_MESSAGES)
        self.max_tokens = self.config.get("max_context_tokens", self.MAX_CONTEXT_TOKENS)
    
    def _build_graph_config(self) -> Optional[Dict[str, Any]]:
        """
        Build graph configuration with optional Langfuse callbacks.
        
        This config is ALWAYS passed to graph.ainvoke(), whether it's None or has callbacks.
        
        Returns:
            Config dict with callbacks if Langfuse enabled, None otherwise
        """
        if not self.enable_langfuse:
            return None
        
        try:
            from langfuse.langchain import CallbackHandler
            
            # Lazy initialize handler
            if self._langfuse_handler is None:
                self._langfuse_handler = CallbackHandler()
                self.logger.info(
                    f"Langfuse tracing initialized for {self.agent_type} agent"
                )
            
            return {"callbacks": [self._langfuse_handler]}
            
        except ImportError:
            self.logger.warning(
                f"Langfuse enabled but not installed for {self.agent_type}. "
                "Install with: pip install langfuse"
            )
            return None
    
    @property
    def graph_config(self) -> Optional[Dict[str, Any]]:
        """
        Get graph configuration for LangGraph execution.
        
        This property returns the config that should ALWAYS be passed to graph.ainvoke().
        Can be None (if Langfuse disabled) or a dict with callbacks (if enabled).
        
        Returns:
            Config dict or None
        """
        return self._graph_config
    
    @property
    def langfuse_config(self) -> Optional[Dict[str, Any]]:
        """
        Deprecated: Use graph_config instead.
        
        Returns:
            Config dict with callbacks if Langfuse enabled, None otherwise
        """
        return self._graph_config
    
    @abstractmethod
    def _build_graph(self):
        """
        Build and compile LangGraph for this agent.
        
        Returns:
            Compiled LangGraph instance
        """
        pass
    
    def truncate_history(
        self,
        history: List[Dict[str, str]],
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Truncate conversation history to fit within context window.
        
        Strategy:
        1. Always keep system message (if present)
        2. Keep most recent messages up to max_history
        3. Estimate tokens and truncate further if needed
        
        Args:
            history: Full conversation history
            include_system: Whether to preserve system message
            
        Returns:
            Truncated history
        """
        if not history:
            return []
        
        truncated = []
        
        # Preserve system message if present
        system_msg = None
        if include_system and history and history[0].get("role") == "system":
            system_msg = history[0]
            history = history[1:]
        
        # Keep most recent messages (in pairs)
        # Each pair = user message + assistant message
        max_messages = self.max_history * 2
        recent_history = history[-max_messages:] if len(history) > max_messages else history
        
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = 0
        if system_msg:
            estimated_tokens += len(str(system_msg.get("content", ""))) // 4
        
        # Add messages from most recent, stopping if token limit exceeded
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
        
        # Add system message back at the beginning
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
        """
        Execute agent with full tracking and memory management.
        
        Args:
            query: User query
            history: Conversation history (will be truncated if needed)
            system_prompt: Optional system prompt
            metadata: Optional metadata
            
        Returns:
            Agent execution result with response
        """
        # Truncate history to fit context window
        truncated_history = self.truncate_history(history or [])
        
        # Build state
        state: ChatState = {
            "query": query,
            "history": truncated_history,
            "system_prompt": system_prompt,
            "metadata": metadata or {},
        }
        
        return await self._execute_internal(state)
    
    async def _execute_internal(self, state: ChatState) -> Dict[str, Any]:
        """
        Internal execution with tracking and optional Langfuse tracing.
        
        Args:
            state: Chat state with truncated history
            
        Returns:
            Execution result
        """
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
            # ALWAYS pass config to graph.ainvoke(), even if it's None
            # This allows LangGraph to handle it properly regardless of Langfuse state
            result = await self.graph.ainvoke(state, config=self.graph_config)
            
            duration = time.time() - start_time
            
            # Log success
            self.logger.info(
                "agent_execution_completed",
                agent_type=self.agent_type,
                duration_ms=int(duration * 1000),
                status="success"
            )
            
            # Track metrics
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
            
            # Log error
            self.logger.error(
                "agent_execution_failed",
                agent_type=self.agent_type,
                duration_ms=int(duration * 1000),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            # Track error metrics
            agent_invocations_total.labels(
                agent_type=self.agent_type,
                status="error"
            ).inc()
            
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get agent configuration.
        
        Returns:
            Configuration dict
        """
        return self.config

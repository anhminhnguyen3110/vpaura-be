"""Base agent class with logging and metrics tracking."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
import time

from ....core.logger import logger as base_logger
from ....middleware.metrics import (
    agent_invocations_total,
    agent_response_time_seconds,
)

from .state import BaseAgentState
from ....config.settings import settings, Environment
from ...utils.message_utils import prepare_messages_for_llm

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


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
        
        self._checkpointer: Optional["AsyncPostgresSaver"] = None
        self._connection_pool: Optional["AsyncConnectionPool"] = None
        
        self.graph = None
        
        self.enable_langfuse = self.config.get("enable_langfuse", settings.LANGFUSE_ENABLED)
        self._langfuse_handler = None
        self._graph_config = None  # Will be built per-request with session context
        
        self.max_history = self.config.get("max_history", self.MAX_HISTORY_MESSAGES)
        self.max_tokens = self.config.get("max_context_tokens", self.MAX_CONTEXT_TOKENS)
    
    async def _get_connection_pool(self) -> Optional["AsyncConnectionPool"]:
        """Get PostgreSQL connection pool for checkpointer."""
        if self._connection_pool is None:
            try:
                from psycopg_pool import AsyncConnectionPool
                
                # Parse DATABASE_URL
                db_url = settings.DATABASE_URL
                # Convert SQLAlchemy URL to psycopg format
                # postgresql+asyncpg://user:pass@host:port/db → postgresql://user:pass@host:port/db
                pg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                
                # Environment-specific pool size
                max_size = {
                    Environment.DEVELOPMENT: 5,
                    Environment.TEST: 3,
                    Environment.STAGING: 10,
                    Environment.PRODUCTION: 20,
                }.get(settings.ENVIRONMENT, 10)
                
                self._connection_pool = AsyncConnectionPool(
                    pg_url,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                
                self.logger.info(
                    "connection_pool_created",
                    max_size=max_size,
                    environment=settings.ENVIRONMENT.value
                )
                
            except Exception as e:
                self.logger.error(
                    "connection_pool_creation_failed",
                    error=str(e),
                    environment=settings.ENVIRONMENT.value
                )
                
                # Production degradation
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    self.logger.warning("continuing_without_checkpointer")
                    return None
                raise
        
        return self._connection_pool
    
    def _build_graph_config(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build graph configuration with optional Langfuse callbacks and session tracking.
        
        Args:
            session_id: Session/thread ID for checkpointer
            user_id: User ID for tracing
            metadata: Additional metadata
            
        Returns:
            Graph configuration dict
        """
        config = {
            "recursion_limit": 100
        }
        
        # Add thread ID for checkpointer if provided
        if session_id:
            config["configurable"] = {"thread_id": session_id}
        
        # Add metadata for tracing
        config["metadata"] = {
            "agent_type": self.agent_type,
            "environment": settings.ENVIRONMENT.value if hasattr(settings, "ENVIRONMENT") else "development",
            **(metadata or {}),
        }
        
        if user_id:
            config["metadata"]["user_id"] = user_id
        
        if session_id:
            config["metadata"]["session_id"] = session_id
        
        # Add Langfuse callback if enabled
        if not self.enable_langfuse:
            return config
        
        try:
            from langfuse.langchain import CallbackHandler
            
            # Create new handler with context or reuse existing
            if session_id or user_id:
                # Create handler with metadata
                # Note: Langfuse CallbackHandler doesn't accept user_id/session_id in __init__
                # These should be passed via metadata or tags
                handler = CallbackHandler()
                config["callbacks"] = [handler]
                
                if not self._langfuse_handler:
                    self.logger.info(
                        "langfuse_tracing_initialized",
                        agent_type=self.agent_type,
                        has_user_id=bool(user_id),
                        has_session_id=bool(session_id)
                    )
            else:
                # Use default handler
                if self._langfuse_handler is None:
                    self._langfuse_handler = CallbackHandler()
                    self.logger.info(
                        "langfuse_tracing_initialized",
                        agent_type=self.agent_type
                    )
                
                config["callbacks"] = [self._langfuse_handler]
            
            return config
            
        except ImportError:
            self.logger.warning(
                "langfuse_enabled_but_not_installed",
                agent_type=self.agent_type,
                hint="Install with: pip install langfuse"
            )
            return config
    
    async def _build_graph_async(self):
        """Build graph with async checkpointer."""
        if self.graph is not None:
            return self.graph
        
        try:
            # Get connection pool
            conn_pool = await self._get_connection_pool()
            
            # Create checkpointer if pool available
            if conn_pool:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                
                self._checkpointer = AsyncPostgresSaver(conn_pool)
                await self._checkpointer.setup()
                
                self.logger.info(
                    "checkpointer_initialized",
                    agent_type=self.agent_type
                )
            else:
                self._checkpointer = None
                self.logger.warning(
                    "no_checkpointer_memory_only",
                    agent_type=self.agent_type
                )
            
            # Build graph (subclass implements _build_graph)
            graph_builder = self._build_graph()
            
            # Compile with checkpointer
            self.graph = graph_builder.compile(
                checkpointer=self._checkpointer
            )
            
            self.logger.info(
                "graph_compiled",
                agent_type=self.agent_type,
                has_checkpointer=self._checkpointer is not None
            )
            
            return self.graph
            
        except Exception as e:
            self.logger.error(
                "graph_build_failed",
                agent_type=self.agent_type,
                error=str(e)
            )
            
            # Production degradation
            if settings.ENVIRONMENT == Environment.PRODUCTION:
                self.logger.warning("continuing_with_basic_graph")
                self.graph = self._build_graph().compile()
                return self.graph
            raise
    
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
        """
        Truncate conversation history to fit within context window.
        
        UPDATED: Now uses prepare_messages_for_llm() with actual LLM tokenizer
        instead of crude len//4 estimation.
        
        Args:
            history: List of message dicts
            include_system: Whether to include system messages (deprecated - handled by prepare_messages_for_llm)
        
        Returns:
            Truncated history that fits within max_tokens
        """
        if not history:
            return []
        
        # Use smart trimming with actual LLM tokenizer
        try:
            from langchain_core.messages import trim_messages, HumanMessage, AIMessage, SystemMessage
            
            # Convert to LangChain messages
            lc_messages = []
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
            
            # Trim using LLM's actual tokenizer
            trimmed = trim_messages(
                lc_messages,
                strategy="last",
                token_counter=self.llm,  # Use actual LLM tokenizer
                max_tokens=self.max_tokens,
                start_on="human",
                include_system=include_system,
                allow_partial=False,
            )
            
            # Convert back to dict format
            result = []
            for msg in trimmed:
                if hasattr(msg, "type"):
                    role_map = {"human": "user", "ai": "assistant", "system": "system"}
                    role = role_map.get(msg.type, "user")
                    result.append({"role": role, "content": msg.content})
            
            if len(result) < len(history):
                self.logger.info(
                    "history_trimmed_by_tokenizer",
                    original_count=len(history),
                    trimmed_count=len(result),
                    max_tokens=self.max_tokens
                )
            
            return result
            
        except Exception as e:
            # Fallback to simple truncation if trim_messages fails
            self.logger.warning(
                "trim_messages_failed_using_fallback",
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Simple fallback: keep last N messages
            max_messages = self.max_history * 2
            truncated = history[-max_messages:] if len(history) > max_messages else history
            
            if len(truncated) < len(history):
                self.logger.info(
                    "history_truncated_by_count",
                    original_count=len(history),
                    truncated_count=len(truncated),
                    max_messages=max_messages
                )
            
            return truncated
    
    async def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute agent with full tracking and memory management."""
        if self.graph is None:
            await self._build_graph_async()
        
        truncated_history = self.truncate_history(history or [])
        
        state: BaseAgentState = {
            "query": query,
            "history": truncated_history,
            "metadata": metadata or {},
        }
        
        # Build config with session tracking
        config = self._build_graph_config(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        return await self._execute_internal(state, config)
    
    async def execute_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Execute agent with streaming response.
        
        Yields tokens as they are generated by the LLM in real-time.
        
        Args:
            query: User query
            session_id: Session ID for checkpointer
            user_id: User ID for tracking
            history: Conversation history
            system_prompt: System prompt for LLM
            metadata: Additional metadata
            
        Yields:
            str: Tokens/chunks as they are generated
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        if self.graph is None:
            await self._build_graph_async()
        
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        for msg in (history or []):
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Build state
        state: BaseAgentState = {
            "messages": messages,
            "session_id": session_id,
            "metadata": metadata or {}
        }
        
        # Build config
        config = self._build_graph_config(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        # Stream execution
        try:
            self.logger.info(
                "agent_stream_started",
                agent_type=self.agent_type,
                session_id=session_id,
                message_count=len(messages)
            )
            
            async for event in self.graph.astream(
                state,
                config=config,
                stream_mode="messages"
            ):
                try:
                    # Extract message from event
                    if isinstance(event, tuple):
                        message, _ = event
                    else:
                        message = event
                    
                    # Get content from message
                    if hasattr(message, "content") and message.content:
                        yield message.content
                        
                except Exception as token_error:
                    self.logger.error(
                        "stream_token_error",
                        error=str(token_error),
                        agent_type=self.agent_type
                    )
                    # Continue streaming despite token error
                    continue
            
            self.logger.info(
                "agent_stream_completed",
                agent_type=self.agent_type,
                session_id=session_id
            )
            
        except Exception as e:
            self.logger.error(
                "agent_stream_failed",
                agent_type=self.agent_type,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _execute_internal(self, state: BaseAgentState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Internal execution with tracking and optional Langfuse tracing."""
        # Use provided config or fall back to self.graph_config
        execution_config = config or self.graph_config
        
        self.logger.info(
            "agent_execution_started",
            agent_type=self.agent_type,
            has_messages=bool(state.get("messages")),
            message_count=len(state.get("messages", [])),
            session_id=state.get("session_id"),
            langfuse_enabled=self.enable_langfuse,
            has_config=execution_config is not None
        )
        
        start_time = time.time()
        
        try:
            result = await self.graph.ainvoke(state, config=execution_config)
            
            duration = time.time() - start_time
            
            # Extract response from messages (last AI message)
            response_text = ""
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    response_text = last_message.content
                else:
                    response_text = str(last_message)
            
            # Add response field for backward compatibility
            result["response"] = response_text
            
            self.logger.info(
                "agent_execution_completed",
                agent_type=self.agent_type,
                duration_ms=int(duration * 1000),
                status="success",
                response_length=len(response_text)
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
    
    async def get_session_history(
        self, 
        session_id: str
    ) -> List[Dict[str, str]]:
        """Get conversation history from checkpointer."""
        if self.graph is None:
            await self._build_graph_async()
        
        if not self._checkpointer:
            self.logger.warning("no_checkpointer_no_history")
            return []
        
        try:
            # Get state from checkpointer
            state_snapshot = self.graph.get_state(
                config={"configurable": {"thread_id": session_id}}
            )
            
            if not state_snapshot.values:
                return []
            
            # Extract messages from state
            messages = state_snapshot.values.get("messages", [])
            
            # Convert to dict format
            history = []
            for msg in messages:
                if hasattr(msg, "type") and msg.type in ["human", "ai"]:
                    history.append({
                        "role": "user" if msg.type == "human" else "assistant",
                        "content": msg.content
                    })
            
            return history
            
        except Exception as e:
            self.logger.error(
                "get_session_history_failed",
                session_id=session_id,
                error=str(e)
            )
            return []
    
    async def clear_session_history(
        self, 
        session_id: str
    ) -> None:
        """Clear checkpointer state for session."""
        if not self._checkpointer:
            self.logger.warning("no_checkpointer_nothing_to_clear")
            return
        
        try:
            conn_pool = await self._get_connection_pool()
            if not conn_pool:
                return
            
            # Delete from checkpoint tables
            checkpoint_tables = settings.CHECKPOINT_TABLES if hasattr(settings, "CHECKPOINT_TABLES") else [
                "checkpoints",
                "checkpoint_writes", 
                "checkpoint_blobs"
            ]
            
            async with conn_pool.connection() as conn:
                for table in checkpoint_tables:
                    try:
                        await conn.execute(
                            f"DELETE FROM {table} WHERE thread_id = %s",
                            (session_id,)
                        )
                        self.logger.info(
                            "cleared_checkpoint_table",
                            table=table,
                            session_id=session_id
                        )
                    except Exception as e:
                        self.logger.error(
                            "clear_table_failed",
                            table=table,
                            error=str(e)
                        )
        
        except Exception as e:
            self.logger.error(
                "clear_session_history_failed",
                session_id=session_id,
                error=str(e)
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config


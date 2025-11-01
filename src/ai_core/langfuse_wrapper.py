"""LangFuse integration for observability (optional)."""

from typing import Optional, Dict, Any
import logging
from functools import wraps

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Try to import LangFuse, but make it optional
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.info("LangFuse not installed. Install with: pip install langfuse")


class LangFuseWrapper:
    """
    Optional LangFuse wrapper for tracing and observability.
    
    Features:
    - Automatic tracing of agent executions
    - Token usage tracking
    - Cost calculation
    - Performance metrics
    
    Usage is completely optional and controlled by LANGFUSE_ENABLED setting.
    """
    
    _instance: Optional['LangFuseWrapper'] = None
    _client: Optional[Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize LangFuse client if enabled."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_client()
    
    def _setup_client(self):
        """Setup LangFuse client if enabled and available."""
        if not settings.LANGFUSE_ENABLED:
            logger.info("LangFuse is disabled (LANGFUSE_ENABLED=False)")
            return
        
        if not LANGFUSE_AVAILABLE:
            logger.warning(
                "LangFuse is enabled but not installed. "
                "Install with: pip install langfuse"
            )
            return
        
        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            logger.warning(
                "LangFuse is enabled but credentials not configured. "
                "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY"
            )
            return
        
        try:
            self._client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            logger.info(f"LangFuse initialized: {settings.LANGFUSE_HOST}")
        except Exception as e:
            logger.error(f"Failed to initialize LangFuse: {e}")
            self._client = None
    
    @property
    def is_enabled(self) -> bool:
        """Check if LangFuse is enabled and available."""
        return (
            settings.LANGFUSE_ENABLED 
            and LANGFUSE_AVAILABLE 
            and self._client is not None
        )
    
    @property
    def client(self) -> Optional[Any]:
        """Get LangFuse client if available."""
        return self._client
    
    def trace_agent(self, agent_name: str):
        """
        Decorator to trace agent execution.
        
        Args:
            agent_name: Name of the agent being traced
            
        Returns:
            Decorator function
        """
        def decorator(func):
            if not self.is_enabled or not LANGFUSE_AVAILABLE:
                # Return unmodified function if LangFuse not available
                return func
            
            @observe(name=agent_name)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def flush(self):
        """Flush pending traces to LangFuse."""
        if self._client:
            try:
                self._client.flush()
            except Exception as e:
                logger.error(f"Failed to flush LangFuse: {e}")


# Global instance
langfuse_wrapper = LangFuseWrapper()


def trace_agent_execution(agent_name: str):
    """
    Decorator for tracing agent executions (if LangFuse enabled).
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Decorator function that may or may not add tracing
    """
    return langfuse_wrapper.trace_agent(agent_name)

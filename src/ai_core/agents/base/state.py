"""Base state definition for all agent workflows.

This module defines the common state structure shared across all agents.
"""

from typing import TypedDict, List, Dict, Optional, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class BaseAgentState(TypedDict):
    """
    Base state for all agent workflows.
    
    This TypedDict defines common fields that all agents share.
    Specific agents can extend this with their own fields.
    
    Attributes:
        messages: Conversation messages with automatic deduplication via add_messages reducer
        session_id: Session/thread ID for checkpointer
        metadata: Additional metadata for the execution
        error: Error message if any occurred during execution
    """
    
    # ✨ NEW: Use add_messages reducer for automatic message management
    # This prevents message duplication and handles tool messages properly
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Session tracking for checkpointer
    session_id: Optional[str]
    
    # Metadata and error tracking
    metadata: Optional[Dict[str, Any]]
    error: Optional[str]

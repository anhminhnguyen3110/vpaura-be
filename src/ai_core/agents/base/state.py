"""Base state definition for all agent workflows.

This module defines the common state structure shared across all agents.
"""

from typing import TypedDict, List, Dict, Optional, Any


class BaseAgentState(TypedDict, total=False):
    """
    Base state for all agent workflows.
    
    This TypedDict defines common fields that all agents share.
    Specific agents can extend this with their own fields.
    
    Attributes:
        query: User input query
        history: Conversation history as list of message dicts
        response: Final agent response to return to user
        error: Error message if any occurred during execution
        metadata: Additional metadata for the execution
    """
    
    query: str
    history: List[Dict[str, str]]
    response: str
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]

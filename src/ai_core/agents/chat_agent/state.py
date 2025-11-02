"""Chat agent state definition."""

from typing import Optional
from ..base import BaseAgentState


class ChatAgentState(BaseAgentState, total=False):
    """
    State for chat agent workflow.
    
    The chat agent is a simple conversational agent that uses
    system prompts to guide the conversation.
    
    Attributes:
        Inherits all fields from BaseAgentState:
            - query: User input query
            - history: Conversation history
            - response: Final response
            - error: Error message if any
            - metadata: Additional metadata
        
        Additional fields:
            system_prompt: System prompt to guide the LLM behavior
    """
    
    system_prompt: Optional[str]

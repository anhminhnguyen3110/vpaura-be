"""Message preparation and cleanup utilities for LangGraph integration."""

from typing import List, Dict, Any, Optional
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    trim_messages,
    convert_to_openai_messages
)
from langchain_core.language_models.chat_models import BaseChatModel

from ...config.settings import settings


def prepare_messages_for_llm(
    messages: List[Dict[str, str]],
    llm: BaseChatModel,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None
) -> List[BaseMessage]:
    """
    Prepare messages for LLM with smart trimming.
    
    Uses LLM's actual tokenizer for accurate token counting.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        llm: LLM instance for token counting
        system_prompt: Optional system prompt to prepend
        max_tokens: Max tokens (defaults to settings.LLM_MAX_TOKENS)
    
    Returns:
        List of prepared LangChain message objects
    """
    # Convert dicts to LangChain messages
    lc_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
    
    # Trim messages to fit context window using LLM's tokenizer
    trimmed = trim_messages(
        lc_messages,
        strategy="last",
        token_counter=llm,  # ✨ Use LLM's actual tokenizer
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        start_on="human",
        include_system=False,
        allow_partial=False,
    )
    
    # Prepend system prompt if provided
    if system_prompt:
        trimmed.insert(0, SystemMessage(content=system_prompt))
    
    return trimmed


def cleanup_response_messages(
    messages: List[BaseMessage]
) -> List[Dict[str, str]]:
    """
    Clean up LLM response messages.
    
    Filters out:
    - System messages
    - Empty messages
    - Tool messages
    
    Args:
        messages: Raw LangChain messages
    
    Returns:
        Clean list of message dicts
    """
    openai_style = convert_to_openai_messages(messages)
    
    cleaned = []
    for msg in openai_style:
        role = msg.get("role")
        content = msg.get("content", "")
        
        # Filter criteria
        if role not in ["user", "assistant"]:
            continue
        if not content or not content.strip():
            continue
        
        cleaned.append({
            "role": role,
            "content": content
        })
    
    return cleaned


def dump_messages(messages: List) -> List[Dict[str, str]]:
    """
    Dump messages to dict format for serialization.
    
    Args:
        messages: List of message objects or dicts
    
    Returns:
        List of message dicts
    """
    dumped = []
    for msg in messages:
        if isinstance(msg, dict):
            dumped.append(msg)
        elif hasattr(msg, "model_dump"):
            dumped.append(msg.model_dump())
        elif hasattr(msg, "dict"):
            dumped.append(msg.dict())
        else:
            dumped.append({
                "role": getattr(msg, "role", "user"),
                "content": str(msg)
            })
    
    return dumped

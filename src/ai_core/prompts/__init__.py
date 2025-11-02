"""Prompt templates for AI agents and tools."""

from .intent_detection_prompts import get_intent_detection_prompt, AGENT_CAPABILITIES
from .tool_prompts import get_think_prompt, get_plan_prompt
from .rag_prompts import (
    get_rag_generation_prompt,
    get_rag_thinking_prompt,
    get_rag_planning_prompt,
    RAG_SYSTEM_PROMPT,
)
from .neo4j_prompts import (
    get_neo4j_analysis_prompt,
    get_neo4j_generation_prompt,
)

__all__ = [
    "get_intent_detection_prompt",
    "AGENT_CAPABILITIES",
    "get_think_prompt",
    "get_plan_prompt",
    "get_rag_generation_prompt",
    "get_rag_thinking_prompt",
    "get_rag_planning_prompt",
    "RAG_SYSTEM_PROMPT",
    "get_neo4j_analysis_prompt",
    "get_neo4j_generation_prompt",
]

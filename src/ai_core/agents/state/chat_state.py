"""Chat state definition for agent workflows.

This module defines the state structure used by agents during execution.
"""

from typing import TypedDict, List, Optional, Dict, Any


class ChatState(TypedDict, total=False):
    """
    State for chat agent workflows.
    
    This TypedDict defines all possible state fields that can be used
    across different agent types. Not all fields are required for all agents.
    
    Common fields:
        query: User input query
        history: Conversation history
        response: Final agent response
        error: Error message if any
    
    Neo4j Agent fields:
        thinking: Analytical reasoning output
        plan: Step-by-step plan
        schema: Database schema
        cypher_query: Generated Cypher query
        validation: Query validation result
        explain: Query execution plan
        results: Query execution results
        attempts: Number of execution attempts
        success: Whether execution succeeded
    
    RAG Agent fields:
        thinking: Analytical reasoning output
        plan: Retrieval strategy plan
        retrieved_docs: Retrieved documents with scores
        reranked_docs: Reranked documents
        answer: Generated answer
        context_used: Number of documents used
        retrieval_count: Total documents retrieved
        metadata_filter: Metadata filters for retrieval
    
    Chat Agent fields:
        system_prompt: System prompt for LLM
    """
    
    # Common fields
    query: str
    history: List[Dict[str, str]]
    response: str
    error: Optional[str]
    
    # System fields
    system_prompt: Optional[str]
    metadata: Optional[Dict[str, Any]]
    
    # Neo4j fields
    thinking: Optional[str]
    plan: Optional[Dict[str, Any]]
    schema: Optional[Dict[str, Any]]
    cypher_query: Optional[str]
    validation: Optional[Dict[str, Any]]
    explain: Optional[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]
    attempts: Optional[int]
    success: Optional[bool]
    
    # RAG fields
    retrieved_docs: Optional[List[tuple]]
    reranked_docs: Optional[List[tuple]]
    answer: Optional[str]
    context_used: Optional[int]
    retrieval_count: Optional[int]
    metadata_filter: Optional[Dict[str, Any]]

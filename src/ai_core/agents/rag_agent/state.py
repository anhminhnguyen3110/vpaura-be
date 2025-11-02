"""RAG agent state definition."""

from typing import Optional, Dict, List, Any
from ..base import BaseAgentState


class RAGAgentState(BaseAgentState, total=False):
    """
    State for RAG agent workflow.
    
    The RAG agent handles document retrieval and generation by:
    1. Analyzing the query to determine retrieval strategy
    2. Planning the retrieval approach
    3. Retrieving relevant documents from vector store
    4. Reranking documents for relevance
    5. Generating answers based on retrieved context
    
    Attributes:
        Inherits all fields from BaseAgentState:
            - query: User input query
            - history: Conversation history
            - response: Final response
            - error: Error message if any
            - metadata: Additional metadata
        
        RAG-specific fields:
            thinking: Analytical reasoning about retrieval strategy
            plan: Retrieval strategy plan
            retrieved_docs: Retrieved documents with relevance scores
            reranked_docs: Reranked documents after reranking step
            answer: Generated answer based on context
            context_used: Number of documents used in generation
            retrieval_count: Total number of documents retrieved
            metadata_filter: Metadata filters applied during retrieval
    """
    
    thinking: Optional[str]
    plan: Optional[Dict[str, Any]]
    retrieved_docs: Optional[List[tuple]]
    reranked_docs: Optional[List[tuple]]
    answer: Optional[str]
    context_used: Optional[int]
    retrieval_count: Optional[int]
    metadata_filter: Optional[Dict[str, Any]]

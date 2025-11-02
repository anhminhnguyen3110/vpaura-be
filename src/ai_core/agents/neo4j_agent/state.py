"""Neo4j agent state definition."""

from typing import Optional, Dict, List, Any
from ..base import BaseAgentState


class Neo4jAgentState(BaseAgentState, total=False):
    """State for Neo4j agent workflow."""
    
    thinking: Optional[str]
    plan: Optional[Dict[str, Any]]
    schema: Optional[Dict[str, Any]]
    cypher_query: Optional[str]
    validation: Optional[Dict[str, Any]]
    explain: Optional[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]
    attempts: Optional[int]
    success: Optional[bool]
    skip_retry: Optional[bool]

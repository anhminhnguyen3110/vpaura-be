"""Neo4j agent for Cypher query generation and execution."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
import asyncio

from ..agents.base import BaseAgent
from ..llm.llm_factory import LLMFactory
from .state.chat_state import ChatState
from ..tools.think import ThinkTool
from ..tools.plan import PlanTool
from ..mcp.neo4j_client import Neo4jMCPClient


class Neo4jAgent(BaseAgent):
    """
    Neo4j agent for Cypher query generation and execution.
    
    This agent uses a full workflow:
    - Think: Analytical reasoning about the query
    - Plan: Step-by-step query planning
    - Generate: Create Cypher query
    - Validate: Check query syntax
    - Explain: Get execution plan
    - Execute: Run query with 3 retries
    - Respond: Format results
    
    Features:
    - Automatic retry logic (3 attempts)
    - Query validation before execution
    - Execution plan explanation
    - Schema-aware query generation
    """
    
    MAX_RETRIES = 3
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        model: Optional[str] = None,
        neo4j_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize Neo4j Agent.
        
        Args:
            llm_provider: LLM provider name (default from config)
            model: Model name (default from config)
            neo4j_config: Neo4j connection config
            **kwargs: Additional configuration
        """
        self.llm = LLMFactory.create(provider=llm_provider, model=model)
        self.neo4j_client = Neo4jMCPClient(config=neo4j_config)
        self.think_tool = ThinkTool()
        self.plan_tool = PlanTool()
        super().__init__(agent_type="neo4j", **kwargs)
    
    def _build_graph(self) -> StateGraph:
        """
        Build Neo4j agent graph.
        
        Graph:
        think → plan → generate → validate → explain → execute → respond → END
        
        Retry logic in execute node (3 attempts).
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("think", self._think_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("explain", self._explain_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("respond", self._respond_node)
        
        # Build workflow
        workflow.set_entry_point("think")
        workflow.add_edge("think", "plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", "validate")
        workflow.add_edge("validate", "explain")
        workflow.add_edge("explain", "execute")
        workflow.add_edge("execute", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    async def _think_node(self, state: ChatState) -> Dict[str, Any]:
        """Think about the query analytically."""
        self.logger.info("Executing think node")
        
        try:
            # Get schema for context
            schema = await self.neo4j_client.get_schema()
            
            # Build thinking prompt
            prompt = f"""
            User Query: {state['query']}
            
            Database Schema:
            - Node Labels: {', '.join(schema.get('node_labels', []))}
            - Relationships: {', '.join(schema.get('relationship_types', []))}
            
            Analyze this query and think about:
            1. What data is the user asking for?
            2. Which nodes and relationships are involved?
            3. What patterns should we match?
            4. Any potential edge cases or considerations?
            """
            
            thinking = await self.think_tool.execute(prompt)
            
            return {
                "thinking": thinking,
                "schema": schema
            }
            
        except Exception as e:
            self.logger.error(f"Think node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _plan_node(self, state: ChatState) -> Dict[str, Any]:
        """Plan the Cypher query steps."""
        self.logger.info("Executing plan node")
        
        try:
            prompt = f"""
            User Query: {state['query']}
            Thinking: {state.get('thinking', '')}
            
            Create a step-by-step plan for generating the Cypher query.
            Consider:
            1. MATCH patterns needed
            2. WHERE conditions
            3. RETURN clause
            4. Optional aggregations or ordering
            """
            
            plan = await self.plan_tool.execute(prompt)
            
            return {"plan": plan}
            
        except Exception as e:
            self.logger.error(f"Plan node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _generate_node(self, state: ChatState) -> Dict[str, Any]:
        """Generate Cypher query."""
        self.logger.info("Executing generate node")
        
        try:
            schema = state.get("schema", {})
            plan = state.get("plan", {})
            
            prompt = f"""
            Generate a Neo4j Cypher query based on:
            
            User Query: {state['query']}
            Plan: {plan.get('steps', [])}
            
            Available Schema:
            - Nodes: {schema.get('node_labels', [])}
            - Relationships: {schema.get('relationship_types', [])}
            
            Return ONLY the Cypher query, no explanation.
            """
            
            messages = [{"role": "user", "content": prompt}]
            cypher_query = await self.llm.ainvoke(messages)
            
            return {"cypher_query": cypher_query.strip()}
            
        except Exception as e:
            self.logger.error(f"Generate node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _validate_node(self, state: ChatState) -> Dict[str, Any]:
        """Validate Cypher query syntax."""
        self.logger.info("Executing validate node")
        
        try:
            cypher_query = state.get("cypher_query", "")
            validation_result = await self.neo4j_client.validate_query(cypher_query)
            
            if not validation_result.get("valid"):
                self.logger.warning(
                    f"Query validation failed: {validation_result.get('error')}"
                )
            
            return {"validation": validation_result}
            
        except Exception as e:
            self.logger.error(f"Validate node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _explain_node(self, state: ChatState) -> Dict[str, Any]:
        """Get query execution plan."""
        self.logger.info("Executing explain node")
        
        try:
            cypher_query = state.get("cypher_query", "")
            explain_result = await self.neo4j_client.explain_query(cypher_query)
            
            return {"explain": explain_result}
            
        except Exception as e:
            self.logger.error(f"Explain node error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _execute_node(self, state: ChatState) -> Dict[str, Any]:
        """
        Execute Cypher query with retry logic.
        
        Retries up to MAX_RETRIES times before failing.
        """
        self.logger.info("Executing execute node with retry logic")
        
        cypher_query = state.get("cypher_query", "")
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self.logger.info(f"Query execution attempt {attempt}/{self.MAX_RETRIES}")
                
                results = await self.neo4j_client.execute_cypher(cypher_query)
                
                self.logger.info(
                    f"Query executed successfully on attempt {attempt}"
                )
                
                return {
                    "results": results,
                    "attempts": attempt,
                    "success": True
                }
                
            except Exception as e:
                self.logger.warning(
                    f"Query execution failed on attempt {attempt}: {str(e)}"
                )
                
                if attempt == self.MAX_RETRIES:
                    # All retries exhausted
                    self.logger.error(
                        f"Query execution failed after {self.MAX_RETRIES} attempts"
                    )
                    return {
                        "error": f"Query execution failed after {self.MAX_RETRIES} attempts: {str(e)}",
                        "attempts": attempt,
                        "success": False
                    }
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                self.logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # Should never reach here, but just in case
        return {
            "error": "Unexpected error in retry logic",
            "success": False
        }
    
    async def _respond_node(self, state: ChatState) -> Dict[str, Any]:
        """Format and return final response."""
        self.logger.info("Executing respond node")
        
        try:
            if not state.get("success"):
                # Query execution failed
                error_msg = state.get("error", "Unknown error")
                response = f"I apologize, but I couldn't execute the query. Error: {error_msg}"
                
                return {
                    "response": response,
                    "error": error_msg
                }
            
            # Success - format results
            results = state.get("results", [])
            cypher_query = state.get("cypher_query", "")
            attempts = state.get("attempts", 1)
            
            # Build response
            response_parts = [
                f"Query executed successfully (attempt {attempts}):",
                f"\nCypher:\n```cypher\n{cypher_query}\n```",
                f"\nResults: {len(results)} record(s) found"
            ]
            
            if results:
                response_parts.append(f"\n\nSample results:\n{results[:3]}")
            
            response = "\n".join(response_parts)
            
            return {
                "response": response,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Respond node error: {str(e)}", exc_info=True)
            return {
                "response": "Error formatting response",
                "error": str(e)
            }

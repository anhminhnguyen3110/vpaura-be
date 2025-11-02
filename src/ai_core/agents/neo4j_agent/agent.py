"""Neo4j agent for Cypher query generation and execution."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
import asyncio

from ..base import BaseAgent
from ...llm.llm_factory import LLMFactory
from .state import Neo4jAgentState
from ...tools.think import ThinkTool
from ...mcp.neo4j_client import Neo4jMCPClient
from ...prompts.neo4j_prompts import (
    get_neo4j_analysis_prompt,
    get_neo4j_generation_prompt
)
from ....config.settings import settings


class Neo4jAgent(BaseAgent):
    """Neo4j agent for Cypher query generation and execution."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Neo4j Agent."""
        config = config or {}
        
        from ...llm.llm_factory import LLMProviderType
        
        self.llm = LLMFactory.create(
            provider_type=LLMProviderType(config.get("llm_provider", settings.LLM_PROVIDER)),
            model=config.get("model", settings.LLM_MODEL),
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=config.get("temperature", 0.3),
            max_tokens=config.get("max_tokens", 1500)
        )
        self.neo4j_client = Neo4jMCPClient(config=config.get("neo4j_config"))
        self.think_tool = ThinkTool()
        self.max_retries = settings.NEO4J_AGENT_MAX_RETRIES
        super().__init__(agent_type="neo4j")
    
    def _build_graph(self) -> StateGraph:
        """Build Neo4j agent workflow graph."""
        workflow = StateGraph(Neo4jAgentState)
        
        workflow.add_node("get_schema", self._get_schema_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("evaluate", self._evaluate_node)
        workflow.add_node("respond", self._respond_node)
        
        workflow.set_entry_point("get_schema")
        workflow.add_edge("get_schema", "analyze")
        workflow.add_edge("analyze", "generate")
        workflow.add_edge("generate", "validate")
        
        workflow.add_conditional_edges(
            "validate",
            self._should_retry_after_validation,
            {
                "execute": "execute",
                "retry": "generate"
            }
        )
        
        workflow.add_edge("execute", "evaluate")
        
        workflow.add_conditional_edges(
            "evaluate",
            self._should_retry_after_evaluation,
            {
                "retry": "generate",
                "respond": "respond"
            }
        )
        
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    def _should_retry_after_validation(self, state: Neo4jAgentState) -> str:
        """Decide if we should retry after validation."""
        validation = state.get("validation", {})
        is_valid = validation.get("valid", False)
        attempt = state.get("attempt", 0)
        skip_retry = state.get("skip_retry", False)
        error = state.get("error", "")
        
        if skip_retry or error:
            self.logger.warning(f"Stopping retry: skip_retry={skip_retry}, has_error={bool(error)}")
            return "execute"
        
        if not is_valid and attempt < self.max_retries:
            return "retry"
        elif not is_valid:
            return "execute"
        else:
            return "execute"
    
    def _should_retry_after_evaluation(self, state: Neo4jAgentState) -> str:
        """Decide if we should retry after evaluation."""
        should_retry = state.get("should_retry", False)
        attempt = state.get("attempt", 0)
        
        if should_retry and attempt < self.max_retries:
            return "retry"
        return "respond"
    
    async def _get_schema_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Fetch Neo4j schema first."""
        self.logger.info("Fetching Neo4j schema")
        
        try:
            schema = await self.neo4j_client.get_schema()
            
            return {
                "schema": schema,
                "attempt": 0
            }
            
        except Exception as e:
            self.logger.error(f"Schema fetch error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _analyze_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Analyze query with schema context."""
        self.logger.info("Analyzing query with schema")
        
        try:
            schema = state.get("schema", {})
            prompt = get_neo4j_analysis_prompt(state['query'], schema)
            analysis = await self.think_tool.execute(prompt)
            
            return {"analysis": analysis}
            
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def _generate_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Generate Cypher query using LLM."""
        self.logger.info("Generating Cypher query")
        
        try:
            schema = state.get("schema", {})
            attempt = state.get("attempt", 0) + 1
            validation = state.get("validation", {})
            
            prompt = get_neo4j_generation_prompt(state['query'], {}, schema)
            
            if attempt > 1 and validation:
                errors = validation.get("errors", [])
                if errors:
                    error_text = "\n".join(f"- {err}" for err in errors)
                    prompt += f"\n\nPREVIOUS ATTEMPT FAILED with errors:\n{error_text}\n\nPlease fix these issues and generate a corrected query."
            
            from langchain_core.messages import HumanMessage
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            cypher_query = self._extract_cypher(response)
            
            self.logger.info(f"Generated Cypher (attempt {attempt}): {cypher_query[:200]}...")
            
            return {
                "cypher_query": cypher_query,
                "attempt": attempt
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Generate error: {error_msg}", exc_info=True)
            
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                self.logger.warning("⚠️ RATE LIMIT EXCEEDED - Please inform user")
                return {
                    "cypher_query": "",
                    "attempt": state.get("attempt", 0) + 1,
                    "error": "⚠️ API rate limit exceeded. Please wait a moment and try again.",
                    "skip_retry": True
                }
            
            return {
                "cypher_query": "",
                "attempt": state.get("attempt", 0) + 1,
                "error": error_msg
            }
    
    def _extract_cypher(self, response: Any) -> str:
        """Extract Cypher query from LLM response."""
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        
        return content.strip()
    
    async def _validate_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Validate Cypher query."""
        self.logger.info("Validating Cypher query")
        
        try:
            cypher_query = state.get("cypher_query", "")
            attempt = state.get("attempt", 1)
            
            validation = await self.neo4j_client.validate_query(cypher_query)
            
            is_valid = validation.get("valid", False)
            errors = validation.get("errors", [])
            warnings = validation.get("warnings", [])
            
            if not is_valid:
                self.logger.warning(f"Validation failed (attempt {attempt}): {errors}")
            else:
                self.logger.info(f"Validation passed (attempt {attempt})")
                if warnings:
                    self.logger.info(f"Warnings: {warnings}")
            
            return {
                "validation": validation,
                "validation_passed": is_valid
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}", exc_info=True)
            return {
                "validation": {"valid": True, "errors": [], "warnings": [f"Validation check failed: {e}"]},
                "validation_passed": True
            }
    
    async def _execute_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Execute Cypher query."""
        self.logger.info("Executing Cypher query")
        
        try:
            cypher_query = state.get("cypher_query", "")
            
            results = await self.neo4j_client.execute_cypher(cypher_query)
            
            self.logger.info(f"Query executed: {len(results)} records returned")
            
            return {
                "results": results,
                "execution_error": None
            }
            
        except Exception as e:
            self.logger.warning(f"Execution error: {str(e)}")
            return {
                "results": [],
                "execution_error": str(e)
            }
    
    async def _evaluate_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Evaluate if results are satisfactory or need retry."""
        self.logger.info("Evaluating query results")
        
        try:
            error = state.get("error", "")
            skip_retry = state.get("skip_retry", False)
            if error or skip_retry:
                self.logger.warning("Skipping evaluation - error present")
                return {
                    "should_retry": False,
                    "evaluation": "SKIP: Error exists"
                }
            
            results = state.get("results", [])
            execution_error = state.get("execution_error")
            validation = state.get("validation", {})
            query = state.get("query", "")
            cypher_query = state.get("cypher_query", "")
            
            validation_errors = validation.get("errors", [])
            if validation_errors:
                return {
                    "should_retry": True,
                    "evaluation": f"RETRY: Validation errors - {', '.join(validation_errors)}"
                }
            
            eval_prompt = f"""Evaluate the Cypher query execution:

User Query: {query}
Generated Cypher: {cypher_query}
Validation Warnings: {validation.get("warnings", [])}
Execution Error: {execution_error or "None"}
Results Count: {len(results)}
Sample Results: {results[:3] if results else "No results"}

Instructions:
Determine if the query execution was successful and results are satisfactory.

Consider:
1. Was there an execution error? If yes, what's the issue?
2. Are the results relevant to the user's query?
3. Is the result count reasonable (not too few, not suspiciously many)?
4. Do validation warnings indicate potential issues?
5. Should we retry with a different/corrected query?

Respond with ONLY:
- "RETRY: <reason>" if we should retry (syntax error, no results when expected, wrong results, etc.)
- "SUCCESS" if results are satisfactory

Your evaluation:"""
            
            response = await self.think_tool.execute(eval_prompt)
            evaluation = response.strip().upper()
            
            should_retry = evaluation.startswith("RETRY")
            
            if should_retry:
                self.logger.info(f"Evaluation suggests retry: {evaluation}")
            else:
                self.logger.info("Evaluation: Query successful")
            
            return {
                "should_retry": should_retry,
                "evaluation": evaluation
            }
            
        except Exception as e:
            self.logger.error(f"Evaluation error: {str(e)}", exc_info=True)
            return {
                "should_retry": False,
                "evaluation": f"ERROR: {str(e)}"
            }
    
    async def _respond_node(self, state: Neo4jAgentState) -> Dict[str, Any]:
        """Format and return final response."""
        self.logger.info("Formatting final response")
        
        try:
            results = state.get("results", [])
            execution_error = state.get("execution_error")
            validation = state.get("validation", {})
            cypher_query = state.get("cypher_query", "")
            attempt = state.get("attempt", 1)
            evaluation = state.get("evaluation", "")
            
            validation_errors = validation.get("errors", [])
            validation_warnings = validation.get("warnings", [])
            
            if validation_errors:
                response = f"""I apologize, but I couldn't generate a valid Cypher query.

**Validation Errors:**
{chr(10).join(f'- {err}' for err in validation_errors)}

**Suggestion:** {validation.get("suggestion", "Please rephrase your question")}

**Last attempted query:**
```cypher
{cypher_query}
```

Please try rephrasing your question or provide more specific details."""
                
                return {
                    "response": response,
                    "error": "Validation failed"
                }
            
            if execution_error and not results:
                response = f"""I apologize, but I couldn't execute the query successfully.

**Error:** {execution_error}

**Evaluation:** {evaluation}

**Query attempted:**
```cypher
{cypher_query}
```
"""
                
                if validation_warnings:
                    response += f"\n**Validation Warnings:**\n{chr(10).join(f'- {w}' for w in validation_warnings)}"
                
                response += "\n\nPlease try rephrasing your question or provide more details."
                
                return {
                    "response": response,
                    "error": execution_error
                }
            
            response_parts = [
                f"✅ Query executed successfully (attempt {attempt}/{self.max_retries})",
                f"\n**Cypher Query:**\n```cypher\n{cypher_query}\n```",
                f"\n**Results:** {len(results)} record(s) found"
            ]
            
            if validation_warnings:
                response_parts.append(
                    f"\n**Validation Warnings:**\n{chr(10).join(f'- {w}' for w in validation_warnings)}"
                )
            
            if results:
                response_parts.append(f"\n**Sample Results:**\n```json\n{results[:5]}\n```")
            
            response = "\n".join(response_parts)
            
            return {
                "response": response,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Response formatting error: {str(e)}", exc_info=True)
            return {
                "response": "Error formatting response",
                "error": str(e)
            }

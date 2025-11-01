"""Think tool for analytical reasoning."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage

from .base import BaseTool
from ..llm import LLMFactory, LLMProviderType
from ...config.settings import settings


class ThinkTool(BaseTool):
    """
    Think tool for step-by-step reasoning.
    
    Inspired by Anthropic's thinking process.
    Uses LLM to analyze and reason about problems.
    """
    
    @property
    def name(self) -> str:
        return "think"
    
    @property
    def description(self) -> str:
        return "Think through a problem step by step before taking action"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute thinking process.
        
        Args:
            params: Must contain "prompt" key with thinking prompt
            
        Returns:
            Dict with "result" key containing thinking output
            
        Example:
            >>> result = await think_tool.execute({
            ...     "prompt": "Analyze this Neo4j query request..."
            ... })
            >>> print(result["result"])
        """
        prompt = params.get("prompt", "")
        
        if not prompt:
            return {
                "result": "No prompt provided",
                "tool": self.name,
                "error": "Missing prompt parameter"
            }
        
        # Create LLM for thinking
        llm = LLMFactory.create(
            provider_type=LLMProviderType(settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=0.3,  # Lower temp for analytical thinking
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            enable_guardrail=False  # No guardrail for internal tools
        )
        
        # Structured thinking prompt
        think_prompt = f"""<think>
{prompt}

Think through this carefully. Analyze the problem step by step.
Provide your reasoning and key insights.
</think>"""
        
        response = await llm.ainvoke([HumanMessage(content=think_prompt)])
        
        return {
            "result": response.content,
            "tool": self.name,
            "prompt_length": len(prompt),
            "response_length": len(response.content)
        }

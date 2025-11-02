"""Think tool for analytical reasoning."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage

from .base import BaseTool
from ..llm import LLMFactory, LLMProviderType
from ..prompts.tool_prompts import get_think_prompt
from ...config.settings import settings


class ThinkTool(BaseTool):
    """Think tool for step-by-step analytical reasoning."""
    
    @property
    def name(self) -> str:
        return "think"
    
    @property
    def description(self) -> str:
        return "Think through a problem step by step before taking action"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute thinking process."""
        prompt = params.get("prompt", "")
        
        if not prompt:
            return {
                "result": "No prompt provided",
                "tool": self.name,
                "error": "Missing prompt parameter"
            }
        
        llm = LLMFactory.create(
            provider_type=LLMProviderType(settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=0.3,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            enable_guardrail=False
        )
        
        think_prompt = get_think_prompt(prompt)
        
        response = await llm.ainvoke([HumanMessage(content=think_prompt)])
        
        return {
            "result": response.content,
            "tool": self.name,
            "prompt_length": len(prompt),
            "response_length": len(response.content)
        }

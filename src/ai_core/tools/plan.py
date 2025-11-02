"""Plan tool for creating step-by-step execution plans."""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from .base import BaseTool
from ..llm import LLMFactory, LLMProviderType
from ..prompts.tool_prompts import get_plan_prompt
from ...config.settings import settings


class PlanTool(BaseTool):
    """
    Plan tool for creating structured execution plans.
    
    Inspired by Anthropic's planning process.
    Breaks down complex tasks into actionable steps.
    """
    
    @property
    def name(self) -> str:
        return "plan"
    
    @property
    def description(self) -> str:
        return "Create a step-by-step plan for executing a complex task"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute planning process.
        
        Args:
            params: Must contain "prompt" key with planning context
            
        Returns:
            Dict with "steps" (list) and "plan_text" (str) keys
            
        Example:
            >>> result = await plan_tool.execute({
            ...     "prompt": "Create plan for generating Cypher query..."
            ... })
            >>> print(result["steps"])
            ["1. Identify nodes", "2. Define relationships", ...]
        """
        prompt = params.get("prompt", "")
        
        if not prompt:
            return {
                "steps": [],
                "plan_text": "No prompt provided",
                "tool": self.name,
                "error": "Missing prompt parameter"
            }
        
        llm = LLMFactory.create(
            provider_type=LLMProviderType(settings.LLM_PROVIDER),
            model=settings.LLM_MODEL,
            temperature=0.2,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            enable_guardrail=False
        )
        
        plan_prompt = get_plan_prompt(prompt)
        
        response = await llm.ainvoke([HumanMessage(content=plan_prompt)])
        plan_text = response.content.strip()
        
        steps = self._parse_steps(plan_text)
        
        return {
            "steps": steps,
            "plan_text": plan_text,
            "tool": self.name,
            "num_steps": len(steps)
        }
    
    def _parse_steps(self, plan_text: str) -> List[str]:
        """
        Parse numbered steps from plan text.
        
        Args:
            plan_text: Raw plan text with numbered steps
            
        Returns:
            List of step strings
        """
        steps = []
        for line in plan_text.split('\n'):
            line = line.strip()
            if line and len(line) > 2:
                if line[0].isdigit() and line[1] in ['.', ')', ':']:
                    steps.append(line)
        
        return steps if steps else [plan_text]

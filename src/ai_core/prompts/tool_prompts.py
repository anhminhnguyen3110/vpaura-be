"""Prompts for AI tools (Think, Plan, etc.)."""


def get_think_prompt(context: str) -> str:
    """Generate thinking prompt.
    
    Args:
        context: Context to think about
        
    Returns:
        Formatted thinking prompt
    """
    return f"""<think>
{context}

Instructions:
- Analyze the situation carefully step by step
- Consider multiple perspectives and approaches
- Identify key insights and potential challenges
- Format: Use clear paragraphs to explain your reasoning
</think>"""


def get_plan_prompt(context: str) -> str:
    """Generate planning prompt.
    
    Args:
        context: Context to plan for
        
    Returns:
        Formatted planning prompt
    """
    return f"""<plan>
{context}

Create a clear, numbered step-by-step plan.
Each step should be specific and actionable.
Format: Use numbered list (1., 2., 3., etc.)
</plan>"""


# Template constants
THINK_PROMPT_TEMPLATE = get_think_prompt
PLAN_PROMPT_TEMPLATE = get_plan_prompt

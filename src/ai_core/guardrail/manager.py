from .content_guardrail import ContentGuardrail
from ...config.settings import settings
from typing import Dict, Any


class GuardrailManager:
    def __init__(self):
        self.enabled = settings.ENABLE_GUARDRAIL
        self.guardrails = [
            ContentGuardrail()
        ]
    
    async def validate_input(self, input_text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "valid": True,
                "reason": None,
                "blocked": False
            }
        
        for guardrail in self.guardrails:
            result = await guardrail.validate_input(input_text)
            if not result["valid"]:
                return result
        
        return {
            "valid": True,
            "reason": None,
            "blocked": False
        }
    
    async def validate_output(self, output_text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "valid": True,
                "reason": None,
                "blocked": False
            }
        
        for guardrail in self.guardrails:
            result = await guardrail.validate_output(output_text)
            if not result["valid"]:
                return result
        
        return {
            "valid": True,
            "reason": None,
            "blocked": False
        }


guardrail_manager = GuardrailManager()

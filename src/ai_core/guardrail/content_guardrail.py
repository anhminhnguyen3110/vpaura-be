from .base import BaseGuardrail
from typing import Dict, Any, List
import re


class ContentGuardrail(BaseGuardrail):
    def __init__(self):
        self.harmful_patterns = [
            r'\b(kill|murder|suicide|harm yourself)\b',
            r'\b(bomb|weapon|explosive|terrorism)\b',
            r'\b(illegal drugs|cocaine|heroin|meth)\b',
        ]
        
        self.toxic_patterns = [
            r'\b(fuck|shit|damn|bitch|asshole)\b',
            r'\b(stupid|idiot|moron|dumb)\b',
        ]
        
        self.competitor_patterns = [
            r'\b(ChatGPT|Claude|Gemini|Copilot|Bard)\b',
        ]
        
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{16}\b',
            r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
        ]
        
        self.max_length = 10000
        self.min_length = 1
    
    async def validate_input(self, input_text: str) -> Dict[str, Any]:
        if not input_text or len(input_text.strip()) < self.min_length:
            return {
                "valid": False,
                "reason": "Input is empty or too short",
                "blocked": True,
                "category": "length"
            }
        
        if len(input_text) > self.max_length:
            return {
                "valid": False,
                "reason": f"Input exceeds maximum length of {self.max_length} characters",
                "blocked": True,
                "category": "length"
            }
        
        violations = []
        
        for pattern in self.harmful_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                violations.append("harmful_content")
                break
        
        for pattern in self.pii_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                violations.append("pii_detected")
                break
        
        if violations:
            return {
                "valid": False,
                "reason": f"Input contains blocked content: {', '.join(violations)}",
                "blocked": True,
                "violations": violations
            }
        
        return {
            "valid": True,
            "reason": None,
            "blocked": False,
            "violations": []
        }
    
    async def validate_output(self, output_text: str) -> Dict[str, Any]:
        if not output_text or len(output_text.strip()) < self.min_length:
            return {
                "valid": False,
                "reason": "Output is empty or too short",
                "blocked": True,
                "category": "length"
            }
        
        if len(output_text) > self.max_length:
            return {
                "valid": False,
                "reason": f"Output exceeds maximum length of {self.max_length} characters",
                "blocked": True,
                "category": "length"
            }
        
        violations = []
        
        for pattern in self.harmful_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                violations.append("harmful_content")
                break
        
        for pattern in self.toxic_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                violations.append("toxic_language")
                break
        
        for pattern in self.competitor_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            if matches:
                violations.append(f"competitor_mention: {', '.join(set(matches))}")
                break
        
        for pattern in self.pii_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                violations.append("pii_leak")
                break
        
        if violations:
            return {
                "valid": False,
                "reason": f"Output contains violations: {', '.join(violations)}",
                "blocked": True,
                "violations": violations
            }
        
        return {
            "valid": True,
            "reason": None,
            "blocked": False,
            "violations": []
        }

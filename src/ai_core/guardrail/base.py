from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseGuardrail(ABC):
    @abstractmethod
    async def validate_input(self, input_text: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def validate_output(self, output_text: str) -> Dict[str, Any]:
        pass

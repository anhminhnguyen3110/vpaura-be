from typing import Dict, Any
from datetime import datetime


class Converter:
    @staticmethod
    def dict_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in data.items():
            snake_key = ''.join(
                ['_' + c.lower() if c.isupper() else c for c in key]
            ).lstrip('_')
            result[snake_key] = value
        return result
    
    @staticmethod
    def model_to_dict(model: Any) -> Dict[str, Any]:
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

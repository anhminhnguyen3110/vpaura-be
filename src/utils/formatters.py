from datetime import datetime
from typing import Any, Dict


class Formatter:
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        return dt.isoformat()
    
    @staticmethod
    def format_response(
        data: Any,
        message: str = "Success",
        status: str = "success"
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def format_error(
        message: str,
        code: str = "ERROR",
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return {
            "status": "error",
            "code": code,
            "message": message,
            "details": details or {}
        }

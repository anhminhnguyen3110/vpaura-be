from typing import Any, Dict, List


class Helpers:
    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        return data.get(key, default)
    
    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for d in dicts:
            result.update(d)
        return result

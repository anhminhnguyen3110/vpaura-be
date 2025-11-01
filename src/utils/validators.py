import re
from typing import Optional
from ..constants.messages import Messages
from ..exceptions.base import ValidationException


class Validator:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationException(Messages.INVALID_EMAIL)
        return True
    
    @staticmethod
    def validate_not_empty(value: str, field_name: str) -> bool:
        if not value or not value.strip():
            raise ValidationException(
                f"{field_name}: {Messages.REQUIRED_FIELD}"
            )
        return True
    
    @staticmethod
    def validate_range(
        value: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> bool:
        if min_val is not None and value < min_val:
            raise ValidationException(f"Value must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationException(f"Value must be <= {max_val}")
        return True

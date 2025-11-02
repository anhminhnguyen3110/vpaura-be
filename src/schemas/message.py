from pydantic import BaseModel
from typing import Optional, Dict, Any
from .base import BaseSchema, TimestampSchema
from ..constants.enums import MessageRole


class MessageBase(BaseSchema):
    content: str
    role: MessageRole


class MessageCreate(MessageBase):
    session_id: int
    extra_data: Optional[Dict[str, Any]] = None


class MessageUpdate(BaseSchema):
    content: str | None = None
    extra_data: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase, TimestampSchema):
    session_id: int
    extra_data: Optional[Dict[str, Any]] = None

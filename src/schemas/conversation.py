from pydantic import BaseModel
from typing import Optional, Dict, Any
from .base import BaseSchema, TimestampSchema


class ConversationBase(BaseSchema):
    title: str


class ConversationCreate(BaseSchema):
    title: str
    user_id: int
    extra_data: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseSchema):
    title: str | None = None
    extra_data: Optional[Dict[str, Any]] = None


class ConversationResponse(TimestampSchema):
    title: str
    user_id: int
    extra_data: Optional[Dict[str, Any]] = None

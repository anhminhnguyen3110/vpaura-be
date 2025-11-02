from pydantic import BaseModel
from typing import Optional, Dict, Any
from .base import BaseSchema, TimestampSchema


class SessionBase(BaseSchema):
    """Base session schema with common fields."""
    name: str


class SessionCreate(BaseSchema):
    """Schema for creating a new session."""
    name: str
    user_id: int
    extra_data: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseSchema):
    """Schema for updating a session."""
    name: str | None = None
    extra_data: Optional[Dict[str, Any]] = None


class SessionResponse(TimestampSchema):
    """Schema for session response."""
    id: int
    name: str
    user_id: int
    extra_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional, Dict, Any
from .base import BaseSchema, TimestampSchema


class DocumentBase(BaseSchema):
    title: str
    content: str


class DocumentCreate(BaseSchema):
    title: str
    content: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    user_id: int


class DocumentUpdate(BaseSchema):
    title: str | None = None
    content: str | None = None
    file_path: str | None = None
    file_type: str | None = None
    extra_data: Optional[Dict[str, Any]] = None


class DocumentResponse(TimestampSchema):
    title: str
    content: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    user_id: int

"""Database models package.

All models inherit from BaseModel which provides:
- Auto-increment ID
- Automatic timestamps (created_at, updated_at)
- to_dict() method for serialization
- Enhanced __repr__() for debugging
"""

from .base import Base, BaseModel
from .user import User
from .conversation import Conversation
from .message import Message
from .document import Document
from .conversation_document import ConversationDocument

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Conversation",
    "Message",
    "Document",
    "ConversationDocument",
]
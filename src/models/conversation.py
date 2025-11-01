from sqlalchemy import Column, Integer, ForeignKey, String, JSON
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from .document import Document


class Conversation(BaseModel):
    __tablename__ = "conversations"
    
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    extra_data = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document",
        secondary="conversation_documents",
        back_populates="conversations"
    )


from sqlalchemy import Column, Integer, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .conversation import Conversation


class Document(BaseModel):
    __tablename__ = "documents"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    extra_data = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="documents")
    conversations = relationship(
        "Conversation",
        secondary="conversation_documents",
        back_populates="documents"
    )


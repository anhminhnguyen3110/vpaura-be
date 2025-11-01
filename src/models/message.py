from sqlalchemy import Column, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel
from ..constants.enums import MessageRole

if TYPE_CHECKING:
    from .conversation import Conversation


class Message(BaseModel):
    __tablename__ = "messages"
    
    content = Column(Text, nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    extra_data = Column(JSON, nullable=True)
    
    conversation = relationship("Conversation", back_populates="messages")


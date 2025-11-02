from sqlalchemy import Column, Integer, ForeignKey, Text, Enum as SQLEnum, JSON, Index, CheckConstraint
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel
from ..constants.enums import MessageRole

if TYPE_CHECKING:
    from .session import Session


class Message(BaseModel):
    """Message model for business persistence.
    
    Stores only final user/assistant messages (no tool calls or system messages).
    LangGraph checkpoints handle full conversation state including tool calls.
    """
    __tablename__ = "messages"
    
    content = Column(Text, nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    extra_data = Column(JSON, nullable=True)
    
    session = relationship("Session", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="check_message_role_business_only"
        ),
        Index('ix_messages_session_created', 'session_id', 'created_at'),
    )


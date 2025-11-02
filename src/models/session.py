from sqlalchemy import Column, Integer, ForeignKey, String, JSON
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from .document import Document


class Session(BaseModel):
    """Chat session model (business entity).
    
    Session ID is used as thread_id for LangGraph checkpointer.
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    extra_data = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    documents = relationship(
        "Document",
        secondary="session_documents",
        back_populates="sessions"
    )

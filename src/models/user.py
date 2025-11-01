from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
from .base import BaseModel

if TYPE_CHECKING:
    from .conversation import Conversation
    from .document import Document


class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    fullname = Column(String(255), nullable=False)
    
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan"
    )


from sqlalchemy import Column, Integer, ForeignKey
from .base import BaseModel


class ConversationDocument(BaseModel):
    __tablename__ = "conversation_documents"
    
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)


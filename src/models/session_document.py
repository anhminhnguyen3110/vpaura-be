from sqlalchemy import Column, Integer, ForeignKey
from .base import BaseModel


class SessionDocument(BaseModel):
    """Junction table for Session-Document many-to-many relationship."""
    __tablename__ = "session_documents"
    
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

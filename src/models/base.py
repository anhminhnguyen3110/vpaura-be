from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


Base = declarative_base()


class BaseModel(Base):
    """Abstract base model with common fields: id, created_at, updated_at."""
    
    __abstract__ = True
    
    id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True, 
        index=True,
        doc="Auto-increment primary key"
    )
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False, 
        doc="Timestamp when record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False, 
        doc="Timestamp when record was last updated"
    )

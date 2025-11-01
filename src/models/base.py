from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


# Create base class for SQLAlchemy 1.4 compatibility
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model class with common fields and functionality.
    
    All models should inherit from this class to get:
    - id: Auto-increment Integer primary key
    - created_at: Timestamp when record was created (auto-set)
    - updated_at: Timestamp when record was last updated (auto-set)
    - to_dict(): Convert model instance to dictionary
    - __repr__(): String representation for debugging
    
    Usage:
        class MyModel(BaseModel):
            __tablename__ = "my_table"
            
            # id, created_at, updated_at are inherited automatically
            name = Column(String(100), nullable=False)
            # ... other fields
    
    Note: This is an abstract class (__abstract__ = True), so SQLAlchemy
    will not create a table for BaseModel itself.
    """
    
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

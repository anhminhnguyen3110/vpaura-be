"""Base vector store interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """Document with metadata."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class BaseVectorStore(ABC):
    """
    Abstract base class for vector stores.
    
    Provides interface for document storage and similarity search.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector store.
        
        Args:
            config: Store configuration
        """
        self.config = config or {}
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs
    ) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of documents to add
            **kwargs: Additional arguments
            
        Returns:
            List of added document IDs
        """
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            **kwargs: Additional arguments
            
        Returns:
            List of similar documents
        """
        pass
    
    @abstractmethod
    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            **kwargs: Additional arguments
            
        Returns:
            List of (document, score) tuples
        """
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs.
        
        Args:
            ids: Document IDs to delete
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_by_ids(self, ids: List[str]) -> List[Document]:
        """
        Get documents by IDs.
        
        Args:
            ids: Document IDs to retrieve
            
        Returns:
            List of documents
        """
        pass

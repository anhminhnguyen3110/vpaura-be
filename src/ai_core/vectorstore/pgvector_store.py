"""Mock pgvector store for development."""

from typing import List, Dict, Any, Optional
import logging
import asyncio
import math
import random

from .base import BaseVectorStore, Document

logger = logging.getLogger(__name__)


class PgVectorStore(BaseVectorStore):
    """
    Mock pgvector store implementation.
    
    This is a MOCK implementation for development.
    Replace with real pgvector implementation when needed.
    
    Features:
    - In-memory document storage
    - Mock embedding similarity search
    - Metadata filtering
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pgvector store.
        
        Args:
            config: Store configuration (connection_string, collection_name, etc.)
        """
        super().__init__(config)
        self._documents: Dict[str, Document] = {}
        self._dimension = config.get("dimension", 1536) if config else 1536
        logger.info(f"Initialized PgVectorStore (MOCK) with dimension={self._dimension}")
    
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs
    ) -> List[str]:
        """
        Add documents to store (mocked).
        
        Args:
            documents: List of documents to add
            **kwargs: Additional arguments
            
        Returns:
            List of added document IDs
        """
        logger.info(f"Adding {len(documents)} documents (MOCK)")
        await asyncio.sleep(0.1)
        
        added_ids = []
        for doc in documents:
            if not doc.embedding:
                doc.embedding = self._generate_mock_embedding()
            
            self._documents[doc.id] = doc
            added_ids.append(doc.id)
        
        logger.info(f"Added {len(added_ids)} documents to store (MOCK)")
        return added_ids
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        """
        Search for similar documents (mocked).
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            **kwargs: Additional arguments
            
        Returns:
            List of similar documents
        """
        results = await self.similarity_search_with_score(
            query=query,
            k=k,
            filter_dict=filter_dict,
            **kwargs
        )
        return [doc for doc, _ in results]
    
    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with scores (mocked).
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Metadata filters
            **kwargs: Additional arguments
            
        Returns:
            List of (document, score) tuples
        """
        logger.info(f"Searching for similar documents (MOCK): '{query[:50]}...'")
        await asyncio.sleep(0.15)
        
        query_embedding = self._generate_mock_embedding(seed=hash(query))
        
        filtered_docs = self._apply_filters(filter_dict)
        
        results = []
        for doc in filtered_docs:
            similarity = self._cosine_similarity(query_embedding, doc.embedding)
            results.append((doc, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:k]
        
        logger.info(f"Found {len(results)} similar documents (MOCK)")
        return results
    
    async def delete_by_ids(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs (mocked).
        
        Args:
            ids: Document IDs to delete
            
        Returns:
            True if successful
        """
        logger.info(f"Deleting {len(ids)} documents (MOCK)")
        await asyncio.sleep(0.05)
        
        for doc_id in ids:
            self._documents.pop(doc_id, None)
        
        logger.info("Deleted documents (MOCK)")
        return True
    
    async def get_by_ids(self, ids: List[str]) -> List[Document]:
        """
        Get documents by IDs (mocked).
        
        Args:
            ids: Document IDs to retrieve
            
        Returns:
            List of documents
        """
        logger.info(f"Retrieving {len(ids)} documents by ID (MOCK)")
        await asyncio.sleep(0.05)
        
        return [self._documents[doc_id] for doc_id in ids if doc_id in self._documents]
    
    def _apply_filters(self, filter_dict: Optional[Dict[str, Any]]) -> List[Document]:
        """
        Apply metadata filters to documents.
        
        Args:
            filter_dict: Metadata filters
            
        Returns:
            Filtered documents
        """
        if not filter_dict:
            return list(self._documents.values())
        
        filtered = []
        for doc in self._documents.values():
            match = True
            for key, value in filter_dict.items():
                if doc.metadata.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(doc)
        
        return filtered
    
    def _generate_mock_embedding(self, seed: Optional[int] = None) -> List[float]:
        """
        Generate mock embedding vector.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            Mock embedding vector
        """
        if seed is not None:
            random.seed(seed)
        
        vector = [random.gauss(0, 1) for _ in range(self._dimension)]
        norm = math.sqrt(sum(x ** 2 for x in vector))
        return [x / norm for x in vector]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get store statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_documents": len(self._documents),
            "dimension": self._dimension,
            "mock": True
        }


# Convenience function to get store instance
def get_pgvector_store(config: Optional[Dict[str, Any]] = None) -> PgVectorStore:
    """
    Get pgvector store instance.
    
    Args:
        config: Store configuration
        
    Returns:
        PgVectorStore instance
    """
    return PgVectorStore(config)

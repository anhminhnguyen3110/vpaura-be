"""Embedding generation utilities."""

from typing import List, Optional
import logging
import asyncio
import random
import math

logger = logging.getLogger(__name__)


class EmbeddingFunction:
    """
    Mock embedding function for development.
    
    This is a MOCK implementation.
    Replace with real embedding model (OpenAI, etc.) when needed.
    """
    
    def __init__(self, dimension: int = 1536):
        """
        Initialize embedding function.
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        logger.info(f"Initialized EmbeddingFunction (MOCK) with dimension={dimension}")
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents (mocked).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} documents (MOCK)")
        await asyncio.sleep(0.1 * len(texts))  # Simulate API call
        
        return [self._generate_embedding(text) for text in texts]
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for query (mocked).
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        logger.info(f"Generating embedding for query (MOCK): '{text[:50]}...'")
        await asyncio.sleep(0.05)  # Simulate API call
        
        return self._generate_embedding(text)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate mock embedding based on text.
        
        Args:
            text: Input text
            
        Returns:
            Normalized embedding vector
        """
        seed = hash(text) % (2 ** 32)
        random.seed(seed)
        
        vector = [random.gauss(0, 1) for _ in range(self.dimension)]
        
        norm = math.sqrt(sum(x ** 2 for x in vector))
        return [x / norm for x in vector]


# Singleton instance
_embedding_function: Optional[EmbeddingFunction] = None


def get_embedding_function(dimension: int = 1536) -> EmbeddingFunction:
    """
    Get embedding function instance (singleton).
    
    Args:
        dimension: Embedding dimension
        
    Returns:
        EmbeddingFunction instance
    """
    global _embedding_function
    
    if _embedding_function is None:
        _embedding_function = EmbeddingFunction(dimension=dimension)
    
    return _embedding_function

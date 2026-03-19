"""Abstract vector store interface for pluggable backends."""

from abc import ABC, abstractmethod
from typing import List

import numpy as np


class BaseVectorStore(ABC):
    """
    Abstract interface for vector storage.
    Implementations: FAISS, Pinecone, Weaviate, Chroma.
    """

    @abstractmethod
    def upsert(
        self,
        namespace: str,
        embeddings: np.ndarray,
        chunks: List[str],
    ) -> None:
        """Store embeddings and chunks under a namespace (e.g. user_id/doc_id)."""
        pass

    @abstractmethod
    def search(
        self,
        namespace: str,
        query_embedding: np.ndarray,
        k: int = 5,
    ) -> List[str]:
        """Search for top-k similar chunks. Returns chunk texts."""
        pass

    @abstractmethod
    def delete(self, namespace: str) -> bool:
        """Remove all vectors for a namespace."""
        pass

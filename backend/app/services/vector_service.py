"""Vector store service - facade over pluggable backends."""

from typing import List

import numpy as np

from app.core.config import settings
from app.core.exceptions import EmbeddingError
from app.services.vector_base import BaseVectorStore
from app.services.vector_faiss import FAISSVectorStore


def _get_vector_backend() -> BaseVectorStore:
    """Factory for vector store backend based on config."""
    if settings.vector_store_type == "faiss":
        return FAISSVectorStore()
    # Future: PineconeVectorStore, WeaviateVectorStore, ChromaVectorStore
    return FAISSVectorStore()


class VectorStore:
    """
    Vector store facade. Uses FAISS by default.
    Supports namespace per user/document for multi-tenancy.
    """

    def __init__(self) -> None:
        self._backend = _get_vector_backend()

    def upsert(
        self,
        document_id: str,
        embeddings: np.ndarray,
        chunks: List[str],
        namespace: str | None = None,
    ) -> None:
        """Upsert embeddings. Uses document_id as namespace if namespace not provided."""
        ns = namespace or document_id
        self._backend.upsert(ns, embeddings, chunks)

    def search(
        self,
        document_id: str,
        query_embedding: np.ndarray,
        k: int = 5,
        namespace: str | None = None,
    ) -> List[str]:
        """Search for similar chunks. Uses document_id as namespace if not provided."""
        ns = namespace or document_id
        return self._backend.search(ns, query_embedding, k)

    def delete(self, document_id: str, namespace: str | None = None) -> bool:
        """Delete vectors for a document."""
        ns = namespace or document_id
        return self._backend.delete(ns)

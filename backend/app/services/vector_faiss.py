"""FAISS vector store implementation with optional disk persistence."""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.core.exceptions import EmbeddingError
from app.core.logging_config import get_logger
from app.services.vector_base import BaseVectorStore

logger = get_logger(__name__)


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-backed vector store with per-namespace indexes.
    Optional: persist indexes to disk under faiss_index_path.
    """

    def __init__(self) -> None:
        self.indexes: Dict[str, faiss.IndexFlatL2] = {}
        self.documents: Dict[str, List[str]] = {}
        self.base_path = Path(settings.faiss_index_path)
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        """Create base directory for persisted indexes."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _namespace_path(self, namespace: str) -> Tuple[Path, Path]:
        """Return (index_path, chunks_path)."""
        safe = namespace.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe}.faiss", self.base_path / f"{safe}.pkl"

    def _persist(self, namespace: str, index: "faiss.Index", chunks: List[str]) -> None:
        """Persist index and chunks to disk for cross-process access."""
        idx_path, chk_path = self._namespace_path(namespace)
        faiss.write_index(index, str(idx_path))
        chk_path.write_bytes(pickle.dumps(chunks))

    def _load_from_disk(self, namespace: str) -> Optional[Tuple["faiss.Index", List[str]]]:
        """Load index and chunks from disk if they exist."""
        idx_path, chk_path = self._namespace_path(namespace)
        if not idx_path.exists() or not chk_path.exists():
            return None
        try:
            index = faiss.read_index(str(idx_path))
            chunks = pickle.loads(chk_path.read_bytes())
            return index, chunks
        except Exception as e:
            logger.warning("Failed to load FAISS index %s: %s", namespace, e)
            return None

    def upsert(
        self,
        namespace: str,
        embeddings: np.ndarray,
        chunks: List[str],
    ) -> None:
        if embeddings.size == 0:
            raise EmbeddingError("No embeddings to store.")
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings.astype("float32"))
        self.indexes[namespace] = index
        self.documents[namespace] = chunks
        self._persist(namespace, index, chunks)

    def search(
        self,
        namespace: str,
        query_embedding: np.ndarray,
        k: int = 5,
    ) -> List[str]:
        index = self.indexes.get(namespace)
        docs = self.documents.get(namespace)
        if index is None or docs is None:
            loaded = self._load_from_disk(namespace)
            if loaded:
                index, docs = loaded
                self.indexes[namespace] = index
                self.documents[namespace] = docs
            else:
                raise EmbeddingError(f"No index found for namespace: {namespace}")

        k = min(k, len(docs))
        distances, indices = index.search(
            query_embedding.astype("float32").reshape(1, -1),
            k,
        )
        results: List[str] = []
        for idx in indices[0]:
            if 0 <= idx < len(docs):
                results.append(docs[idx])
        return results

    def delete(self, namespace: str) -> bool:
        if namespace in self.indexes:
            del self.indexes[namespace]
        if namespace in self.documents:
            del self.documents[namespace]
        idx_path, chk_path = self._namespace_path(namespace)
        for p in (idx_path, chk_path):
            if p.exists():
                p.unlink()
        return True

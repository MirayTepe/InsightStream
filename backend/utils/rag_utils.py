from typing import List
import numpy as np

def embed_chunks(chunks: List[str]) -> np.ndarray:
    if not chunks:
        return np.empty((0, 128), dtype="float32")

    dim = 128
    rng = np.random.default_rng(seed=42)
    embeddings = rng.normal(size=(len(chunks), dim)).astype("float32")
    return embeddings

def build_faiss_index(embeddings: np.ndarray):
    # Geçici olarak FAISS kullanmıyoruz, sadece None döndürüyoruz.
    return None
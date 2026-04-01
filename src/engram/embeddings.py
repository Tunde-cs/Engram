"""Embedding generation and cosine similarity.

Uses sentence-transformers with all-MiniLM-L6-v2 for embeddings.
Model is loaded lazily on first use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
_model_name: str = "all-MiniLM-L6-v2"
_model_version: str = ""


def get_model() -> SentenceTransformer:
    global _model, _model_version
    if _model is None:
        from sentence_transformers import SentenceTransformer
        import sentence_transformers

        _model = SentenceTransformer(_model_name)
        _model_version = sentence_transformers.__version__
    return _model


def get_model_name() -> str:
    return _model_name


def get_model_version() -> str:
    global _model_version
    if not _model_version:
        get_model()  # triggers version capture
    return _model_version


def encode(text: str) -> np.ndarray:
    """Encode text to a normalized embedding vector."""
    model = get_model()
    emb = model.encode(text, normalize_embeddings=True)
    return np.asarray(emb, dtype=np.float32)


def embedding_to_bytes(emb: np.ndarray) -> bytes:
    """Serialize a float32 numpy array to bytes for SQLite BLOB storage."""
    return emb.astype(np.float32).tobytes()


def bytes_to_embedding(data: bytes) -> np.ndarray:
    """Deserialize bytes back to a float32 numpy array."""
    return np.frombuffer(data, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors. Assumes normalized inputs."""
    return float(np.dot(a, b))


def cosine_similarity_batch(query: np.ndarray, candidates: list[np.ndarray]) -> list[float]:
    """Cosine similarity between a query and multiple candidates."""
    if not candidates:
        return []
    matrix = np.stack(candidates)
    scores = matrix @ query
    return scores.tolist()

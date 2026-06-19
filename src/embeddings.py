"""Local embedding model wrapper (Sentence-Transformers).

Loads the model once (it is a few hundred MB and slow to initialise) and reuses
it for both ingestion and query time. Runs fully offline — no API cost.
"""
from __future__ import annotations

from functools import lru_cache

from .config import settings


@lru_cache(maxsize=1)
def get_embedder():
    """Return a cached SentenceTransformer instance."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)

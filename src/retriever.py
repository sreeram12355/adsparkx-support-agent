"""Retrieval over the FAISS vector store.

Returns the top-k most similar chunks for a query along with cosine similarity
scores (the index stores L2-normalised vectors, so inner product == cosine).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import faiss
import numpy as np

from .config import settings, INDEX_PATH
from .embeddings import get_embedder
from .ingest import Chunk, index_exists, load_chunks


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float  # cosine similarity in [-1, 1], typically [0, 1] here


class Retriever:
    def __init__(self):
        if not index_exists():
            raise RuntimeError(
                "Vector index not found. Build it first with:  python -m src.ingest"
            )
        self.index = faiss.read_index(str(INDEX_PATH))
        self.chunks: List[Chunk] = load_chunks()
        self.embedder = get_embedder()

    def search(self, query: str, top_k: int | None = None) -> List[RetrievedChunk]:
        top_k = top_k or settings.top_k
        vec = self.embedder.encode([query])
        vec = np.asarray(vec, dtype="float32")
        faiss.normalize_L2(vec)
        scores, idxs = self.index.search(vec, top_k)

        results: List[RetrievedChunk] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append(RetrievedChunk(chunk=self.chunks[idx], score=float(score)))
        return results

    @staticmethod
    def best_score(results: List[RetrievedChunk]) -> float:
        return results[0].score if results else 0.0

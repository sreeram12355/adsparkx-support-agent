"""Central, configurable settings for the support agent.

Every tunable knob (models, retrieval depth, escalation thresholds, and the
keyword rules that drive escalation) lives here so behaviour can be changed
without touching application logic. Values fall back to environment variables
(loaded from a local .env) and then to sane defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# --- Project paths -----------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
STORAGE_DIR = ROOT_DIR / "storage"          # FAISS index + chunk metadata
INDEX_PATH = STORAGE_DIR / "faiss.index"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"

# Load .env from the project root explicitly so it works regardless of the
# current working directory (e.g. when launched by an external tool).
load_dotenv(ROOT_DIR / ".env")


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # --- LLM (Google Gemini) ---
    # Accept either GOOGLE_API_KEY or GEMINI_API_KEY for convenience.
    google_api_key: str = field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY", "")
    )
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )

    # --- Embeddings (local Sentence-Transformers) ---
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )

    # --- Chunking ---
    chunk_size: int = 700          # characters per chunk (approx.)
    chunk_overlap: int = 120       # character overlap between consecutive chunks

    # --- Retrieval ---
    top_k: int = field(default_factory=lambda: _get_int("TOP_K", 4))
    # Minimum cosine similarity for a chunk to be considered "relevant".
    min_retrieval_score: float = field(
        default_factory=lambda: _get_float("MIN_RETRIEVAL_SCORE", 0.30)
    )

    # --- Escalation (configurable triggers) ---
    max_dissatisfaction_turns: int = field(
        default_factory=lambda: _get_int("MAX_DISSATISFACTION_TURNS", 2)
    )
    # If the best retrieval score is below this, treat the KB as having no
    # relevant answer and escalate.
    escalate_below_score: float = field(
        default_factory=lambda: _get_float("MIN_RETRIEVAL_SCORE", 0.30)
    )

    # Keywords that mark a query as account-sensitive -> always escalate.
    sensitive_keywords: List[str] = field(
        default_factory=lambda: [
            "refund", "chargeback", "charged twice", "double charged", "dispute",
            "lawsuit", "legal", "lawyer", "gdpr", "right to erasure", "delete my data",
            "data breach", "breach", "hacked", "fraud", "unauthorized charge",
            "cancel my account", "close my account", "delete my account",
            "invoice dispute", "billing error", "tax", "vat", "compliance",
        ]
    )

    # Phrases that signal the user explicitly wants a human.
    human_request_keywords: List[str] = field(
        default_factory=lambda: [
            "talk to a human", "speak to a human", "real person", "human agent",
            "talk to an agent", "speak to someone", "representative", "escalate",
        ]
    )

    @property
    def has_api_key(self) -> bool:
        return bool(self.google_api_key and self.google_api_key.strip())


settings = Settings()

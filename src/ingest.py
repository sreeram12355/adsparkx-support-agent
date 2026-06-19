"""Document ingestion: load -> chunk -> embed -> store in FAISS.

Supports Markdown, TXT, PDF, and DOCX. Each chunk carries metadata:
  - source:  the document file name
  - section: nearest Markdown heading / section title (md, txt, docx)
  - page:    1-based page number (PDF)

Run as a script to (re)build the vector index:
    python -m src.ingest
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np

from .config import settings, DATA_DIR, STORAGE_DIR, INDEX_PATH, CHUNKS_PATH
from .embeddings import get_embedder


@dataclass
class Chunk:
    text: str
    source: str
    section: Optional[str] = None
    page: Optional[int] = None

    def citation(self) -> str:
        loc = ""
        if self.page is not None:
            loc = f" (p.{self.page})"
        elif self.section:
            loc = f" — {self.section}"
        return f"{self.source}{loc}"


# --- Loaders -----------------------------------------------------------------

def _load_text_file(path: Path) -> List[tuple[str, Optional[str]]]:
    """Return list of (text_block, section) using Markdown headings as sections."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    blocks: List[tuple[str, Optional[str]]] = []
    current_section: Optional[str] = None
    buffer: List[str] = []

    def flush():
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                blocks.append((text, current_section))
            buffer.clear()

    for line in raw.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            flush()
            current_section = heading.group(2).strip()
        else:
            buffer.append(line)
    flush()
    if not blocks:  # no headings at all
        blocks = [(raw.strip(), None)]
    return blocks


def _load_pdf(path: Path) -> List[tuple[str, int]]:
    """Return list of (page_text, page_number)."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: List[tuple[str, int]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((text, i))
    return pages


def _load_docx(path: Path) -> List[tuple[str, Optional[str]]]:
    """Return list of (text_block, section) using heading styles as sections."""
    import docx

    document = docx.Document(str(path))
    blocks: List[tuple[str, Optional[str]]] = []
    current_section: Optional[str] = None
    buffer: List[str] = []

    def flush():
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                blocks.append((text, current_section))
            buffer.clear()

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style and para.style.name.lower().startswith("heading"):
            flush()
            current_section = text
        else:
            buffer.append(text)
    flush()
    return blocks


# --- Chunking ----------------------------------------------------------------

def _split(text: str, size: int, overlap: int) -> List[str]:
    """Character-based splitter that prefers paragraph/sentence boundaries."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # try to break on a paragraph, then sentence, then space
            window = text[start:end]
            for sep in ("\n\n", "\n", ". ", " "):
                idx = window.rfind(sep)
                if idx > size * 0.5:
                    end = start + idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_chunks() -> List[Chunk]:
    """Load every supported document in DATA_DIR and split into chunks."""
    chunks: List[Chunk] = []
    files = sorted(p for p in DATA_DIR.iterdir() if p.is_file())
    for path in files:
        suffix = path.suffix.lower()
        if suffix in (".md", ".markdown", ".txt"):
            for text, section in _load_text_file(path):
                for piece in _split(text, settings.chunk_size, settings.chunk_overlap):
                    chunks.append(Chunk(piece, path.name, section=section))
        elif suffix == ".pdf":
            for text, page in _load_pdf(path):
                for piece in _split(text, settings.chunk_size, settings.chunk_overlap):
                    chunks.append(Chunk(piece, path.name, page=page))
        elif suffix == ".docx":
            for text, section in _load_docx(path):
                for piece in _split(text, settings.chunk_size, settings.chunk_overlap):
                    chunks.append(Chunk(piece, path.name, section=section))
        # silently skip unsupported file types
    return chunks


# --- Index build / load ------------------------------------------------------

def build_index() -> int:
    """Build the FAISS index from documents in DATA_DIR. Returns chunk count."""
    chunks = build_chunks()
    if not chunks:
        raise RuntimeError(f"No documents found in {DATA_DIR}")

    embedder = get_embedder()
    vectors = embedder.encode([c.text for c in chunks])
    vectors = np.asarray(vectors, dtype="float32")
    faiss.normalize_L2(vectors)  # cosine similarity via inner product

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in chunks], f, ensure_ascii=False, indent=2)

    return len(chunks)


def index_exists() -> bool:
    return INDEX_PATH.exists() and CHUNKS_PATH.exists()


def load_chunks() -> List[Chunk]:
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        return [Chunk(**d) for d in json.load(f)]


if __name__ == "__main__":
    print(f"Ingesting documents from {DATA_DIR} ...")
    count = build_index()
    print(f"Done. Indexed {count} chunks -> {INDEX_PATH}")

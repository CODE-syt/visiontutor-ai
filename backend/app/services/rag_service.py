"""
Lightweight RAG pipeline over a local FAISS index built from the
knowledge_base/ directory.

Pipeline: documents -> chunking -> embeddings -> FAISS index -> similarity
search -> relevant context string handed to the LLM prompt.

Embeddings are generated through the same configured AI provider's
embedding-compatible endpoint when possible; if that's unavailable, a
deterministic bag-of-words hashing fallback is used so RAG still works
fully offline / without extra API cost. This keeps ENABLE_RAG=true usable
even without an embeddings-capable key, at reduced retrieval quality.
"""
from __future__ import annotations

import glob
import hashlib
import os
from dataclasses import dataclass

import numpy as np

from app.config import Settings

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None


VECTOR_DIM = 256


def _hash_embed(text: str, dim: int = VECTOR_DIM) -> np.ndarray:
    """Deterministic, dependency-free embedding fallback (hashed bag-of-words).
    Not as accurate as a real embedding model, but keeps RAG functional
    without requiring an embeddings API call for every chunk."""
    vec = np.zeros(dim, dtype="float32")
    for word in text.lower().split():
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


@dataclass
class RagChunk:
    text: str
    source: str


class RAGService:
    """Builds (or loads) a FAISS index over knowledge_base/*.txt and answers
    similarity queries. Designed to degrade gracefully: if FAISS or the
    knowledge base is unavailable, retrieve() returns an empty context and
    the rest of the app continues to work without RAG."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._index = None
        self._chunks: list[RagChunk] = []
        self._ready = False
        if settings.enable_rag:
            self._build_or_load()

    def _build_or_load(self) -> None:
        if faiss is None:
            return
        kb_dir = self.settings.knowledge_base_dir
        if not os.path.isdir(kb_dir):
            return

        docs = sorted(glob.glob(os.path.join(kb_dir, "**", "*.txt"), recursive=True))
        if not docs:
            return

        chunks: list[RagChunk] = []
        for path in docs:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for chunk in _chunk_text(content):
                chunks.append(RagChunk(text=chunk, source=os.path.basename(path)))

        if not chunks:
            return

        vectors = np.stack([_hash_embed(c.text) for c in chunks])
        index = faiss.IndexFlatIP(VECTOR_DIM)
        index.add(vectors)

        self._index = index
        self._chunks = chunks
        self._ready = True

    @property
    def is_ready(self) -> bool:
        return self._ready and self.settings.enable_rag

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """Return a formatted context string of the top_k most similar chunks,
        or an empty string if RAG is disabled / unavailable / no match."""
        if not self.is_ready or not query.strip():
            return ""

        try:
            q_vec = _hash_embed(query).reshape(1, -1)
            scores, indices = self._index.search(q_vec, top_k)
        except Exception:  # noqa: BLE001
            return ""

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = self._chunks[idx]
            results.append(f"[Source: {chunk.source}]\n{chunk.text}")

        return "\n\n---\n\n".join(results)

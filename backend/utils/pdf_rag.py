"""Full-text Retrieval-Augmented Generation over papers.

This is the piece the README advertised but never had: instead of only looking
at abstracts, we download/parse a paper's full text, split it into overlapping
chunks, embed them, and retrieve the chunks most relevant to a query. Every
retrieved passage carries its source paper id and character span so anything
built on top (e.g. the claim-verification engine) can quote a *verifiable*
location rather than paraphrasing from memory.

Design notes
------------
* The embedder is injected (dependency injection) and only needs:
      .encode(list[str]) -> 2D array-like of shape (n, dim)
      .encode_single(str) -> 1D array-like of shape (dim,)
  The project's EmbeddingModel satisfies this, and tests pass a tiny mock,
  so the module is exercisable without downloading sentence-transformers.
* Retrieval uses cosine similarity computed with numpy. No FAISS dependency
  here on purpose -- full-text chunk indices are per-session and small enough
  that an exact numpy search is simpler and just as correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence
import re

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]): ...
    def encode_single(self, text: str): ...


@dataclass
class Chunk:
    """A contiguous slice of a paper's full text."""
    paper_id: str
    text: str
    start_char: int
    end_char: int
    chunk_index: int
    paper_title: str = ""
    url: str = ""

    def locator(self) -> str:
        """Human-readable pointer to where this passage lives."""
        title = self.paper_title or self.paper_id
        return f"{title} [chars {self.start_char}-{self.end_char}]"


@dataclass
class RetrievedPassage:
    chunk: Chunk
    score: float


def chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 150,
) -> List[tuple]:
    """Split text into overlapping windows, snapping to sentence boundaries.

    Returns a list of (chunk_text, start_char, end_char). Overlap preserves
    context that would otherwise be severed at a window edge.
    """
    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(overlap, chunk_size - 1))

    # Sentence boundaries to snap to, so chunks don't cut mid-sentence.
    boundaries = [m.end() for m in re.finditer(r"[.!?]\s", text)]
    boundaries.append(len(text))

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        target_end = min(start + chunk_size, n)
        # Snap end forward to the nearest sentence boundary within reach.
        snapped = next((b for b in boundaries if b >= target_end), target_end)
        end = min(snapped, n) if snapped - start <= chunk_size * 1.5 else target_end
        piece = text[start:end].strip()
        if piece:
            chunks.append((piece, start, end))
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


class PaperRAGIndex:
    """In-memory full-text chunk index with cosine retrieval."""

    def __init__(self, embedder: Embedder, chunk_size: int = 900, overlap: int = 150):
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunks: List[Chunk] = []
        self._matrix: Optional[np.ndarray] = None  # (n_chunks, dim), L2-normalized

    @property
    def num_chunks(self) -> int:
        return len(self._chunks)

    def indexed_paper_ids(self) -> set:
        return {c.paper_id for c in self._chunks}

    def add_paper(self, paper_id: str, full_text: str, title: str = "", url: str = "") -> int:
        """Chunk, embed and index one paper's full text. Returns chunks added."""
        if paper_id in self.indexed_paper_ids():
            return 0
        raw_chunks = chunk_text(full_text, self.chunk_size, self.overlap)
        if not raw_chunks:
            return 0

        new_chunks = [
            Chunk(
                paper_id=paper_id,
                text=ct,
                start_char=s,
                end_char=e,
                chunk_index=len(self._chunks) + i,
                paper_title=title,
                url=url,
            )
            for i, (ct, s, e) in enumerate(raw_chunks)
        ]

        vectors = np.asarray(self.embedder.encode([c.text for c in new_chunks]), dtype="float32")
        vectors = _l2_normalize(vectors)

        self._chunks.extend(new_chunks)
        self._matrix = vectors if self._matrix is None else np.vstack([self._matrix, vectors])
        return len(new_chunks)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        paper_ids: Optional[Sequence[str]] = None,
    ) -> List[RetrievedPassage]:
        """Return the top-k most similar chunks to the query.

        If paper_ids is given, retrieval is restricted to those papers
        (e.g. "answer this only from paper 3").
        """
        if self._matrix is None or not self._chunks:
            return []

        q = np.asarray(self.embedder.encode_single(query), dtype="float32").reshape(1, -1)
        q = _l2_normalize(q)
        sims = (self._matrix @ q.T).ravel()  # cosine, since both normalized

        allowed = set(paper_ids) if paper_ids else None
        order = np.argsort(-sims)
        results: List[RetrievedPassage] = []
        for idx in order:
            chunk = self._chunks[idx]
            if allowed is not None and chunk.paper_id not in allowed:
                continue
            results.append(RetrievedPassage(chunk=chunk, score=float(sims[idx])))
            if len(results) >= k:
                break
        return results


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms

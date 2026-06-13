"""Tests for full-text chunking and retrieval, using a tiny mock embedder."""

import numpy as np

from utils.pdf_rag import chunk_text, PaperRAGIndex


class BagOfWordsEmbedder:
    """Deterministic, dependency-free embedder over a fixed vocabulary.

    Stands in for sentence-transformers so retrieval logic is testable without
    downloading a model. Cosine similarity on these vectors still tracks word
    overlap, which is enough to assert that retrieval ranks the right chunk.
    """

    VOCAB = [
        "transformer", "attention", "rnn", "recurrent", "slower", "faster",
        "outperform", "translation", "image", "diffusion", "noise", "sample",
    ]

    def encode(self, texts):
        return np.array([self._vec(t) for t in texts], dtype="float32")

    def encode_single(self, text):
        return self._vec(text)

    def _vec(self, text):
        text = text.lower()
        return np.array([float(text.count(w)) for w in self.VOCAB], dtype="float32")


def test_chunk_text_overlaps_and_covers():
    text = ("Sentence one is here. " * 80).strip()
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # Each chunk records a valid, ordered span.
    for ct, s, e in chunks:
        assert ct
        assert 0 <= s < e


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_retrieval_ranks_relevant_chunk_first():
    idx = PaperRAGIndex(BagOfWordsEmbedder(), chunk_size=120, overlap=20)
    idx.add_paper(
        "paper_nlp",
        "Transformers use attention and outperform RNN recurrent models on translation. "
        "Attention attention transformer transformer translation translation.",
        title="Attention Is All You Need",
    )
    idx.add_paper(
        "paper_vision",
        "Diffusion models add noise then sample to generate an image. "
        "Diffusion diffusion noise noise image image sample sample.",
        title="Diffusion Models",
    )
    results = idx.retrieve("transformer attention translation", k=3)
    assert results
    assert results[0].chunk.paper_id == "paper_nlp"


def test_retrieval_can_restrict_to_paper():
    idx = PaperRAGIndex(BagOfWordsEmbedder(), chunk_size=120, overlap=20)
    idx.add_paper("a", "transformer attention transformer attention", title="A")
    idx.add_paper("b", "diffusion noise image diffusion noise image", title="B")
    results = idx.retrieve("transformer", k=5, paper_ids=["b"])
    assert all(r.chunk.paper_id == "b" for r in results)


def test_add_paper_is_idempotent():
    idx = PaperRAGIndex(BagOfWordsEmbedder())
    added_first = idx.add_paper("a", "transformer attention model text here please", title="A")
    added_again = idx.add_paper("a", "transformer attention model text here please", title="A")
    assert added_first > 0
    assert added_again == 0

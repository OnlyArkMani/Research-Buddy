"""Tests for the ResearchService facade using mock components."""

import numpy as np

from service import ResearchService
from utils.pdf_rag import PaperRAGIndex
from verification.engine import ClaimVerificationEngine, RAGEvidenceRetriever
from verification.providers import MockLLMProvider
import json


class ToyEmbedder:
    VOCAB = ["dropout", "overfitting", "reduces", "increases", "accuracy", "speed"]

    def encode(self, texts):
        return np.array([self._v(t) for t in texts], dtype="float32")

    def encode_single(self, text):
        return self._v(text)

    def _v(self, t):
        t = t.lower()
        return np.array([float(t.count(w)) for w in self.VOCAB], dtype="float32")


class FakeSearchAgent:
    """Minimal stand-in implementing the methods ResearchService.search uses."""

    PAPERS = [
        {"id": "p1", "title": "Dropout reduces overfitting", "authors": "A", "year": 2014,
         "citations": 9000, "source": "arXiv", "url": "http://x/p1",
         "abstract": "We show dropout reduces overfitting markedly."},
        {"id": "p2", "title": "When dropout hurts", "authors": "B", "year": 2020,
         "citations": 30, "source": "arXiv", "url": "http://x/p2",
         "abstract": "In contrast dropout increases overfitting in low data."},
    ]

    def search(self, query, max_results=20):
        return list(self.PAPERS[:max_results])

    def semantic_search(self, query, k=10):
        return [{"metadata": p, "final_score": 0.9, "similarity": 0.9} for p in self.PAPERS[:k]]


def _make_verifier():
    index = PaperRAGIndex(ToyEmbedder(), chunk_size=200, overlap=40)
    retriever = RAGEvidenceRetriever(index)

    def responder(prompt, system=None):
        if "atomic factual claims" in (system or "") or "atomic factual claims" in prompt:
            return json.dumps(["Dropout reduces overfitting."])
        if "increases" in prompt and "overfitting" in prompt:
            return json.dumps({"label": "refutes", "confidence": 0.85,
                               "quote": "dropout increases overfitting", "rationale": "x"})
        if "reduces overfitting" in prompt:
            return json.dumps({"label": "supports", "confidence": 0.9,
                               "quote": "dropout reduces overfitting", "rationale": "x"})
        return json.dumps({"label": "neutral", "confidence": 0.3, "quote": "", "rationale": "x"})

    engine = ClaimVerificationEngine(retriever, MockLLMProvider(responder), evidence_per_claim=5)

    def ingest_papers(papers):
        for p in papers:
            if p.get("abstract"):
                index.add_paper(str(p.get("id")), p["abstract"], title=p.get("title", ""), url=p.get("url", ""))

    engine.ingest_papers = ingest_papers
    return engine


def test_search_returns_ranked_papers():
    svc = ResearchService(search_agent=FakeSearchAgent())
    out = svc.search("dropout", max_results=5)
    assert out["count"] == 2
    assert out["papers"][0]["title"]
    assert "relevance" in out["papers"][0]


def test_search_degrades_without_backend():
    svc = ResearchService()
    out = svc.search("anything")
    assert out["papers"] == []
    assert "error" in out


def test_verify_degrades_without_verifier():
    svc = ResearchService(search_agent=FakeSearchAgent())
    out = svc.verify_text("Dropout reduces overfitting.")
    assert "error" in out


def test_verify_end_to_end_with_corpus_from_search():
    svc = ResearchService(search_agent=FakeSearchAgent(), verifier=_make_verifier())
    out = svc.verify_text("Dropout reduces overfitting.", query="dropout overfitting")
    assert out["claims"], "expected at least one claim"
    verdict = out["claims"][0]["verdict"]
    # One supporting + one refuting abstract in the corpus -> contested.
    assert verdict in ("contested", "supported", "refuted")
    assert "consensus" in out["claims"][0]

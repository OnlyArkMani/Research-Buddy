"""ResearchService — the decoupled application layer.

All business logic lives here, returning plain dicts, so every front end
(FastAPI, the old Chainlit UI, a CLI, or tests) is just a thin client. This is
the carve-out described in STRATEGY.md §5: logic must not live inside the UI.

Design:
* Components are injected, so tests construct a service with mocks and never
  touch the network or download models.
* ``create_default()`` builds the real components lazily and degrades
  gracefully — a missing Gemini key or unreachable Ollama disables the LLM-
  dependent paths instead of crashing the whole service.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ResearchService:
    def __init__(
        self,
        search_agent=None,
        verifier=None,
        embedder=None,
        llm_available: bool = False,
    ):
        self.search_agent = search_agent
        self.verifier = verifier          # ClaimVerificationEngine or None
        self.embedder = embedder
        self.llm_available = llm_available

    # ------------------------------------------------------------------ search
    def search(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        if not self.search_agent:
            return {"query": query, "papers": [], "error": "search backend unavailable"}
        papers = self.search_agent.search(query, max_results=max_results)
        ranked = self.search_agent.semantic_search(query, k=min(max_results, len(papers) or 1))
        out = []
        for r in ranked[:max_results]:
            p = r.get("metadata", {})
            out.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "authors": p.get("authors"),
                "year": p.get("year"),
                "citations": p.get("citations", 0),
                "source": p.get("source"),
                "url": p.get("url"),
                "pdf_url": p.get("pdf_url"),
                "abstract": p.get("abstract", ""),
                "relevance": round(float(r.get("final_score", r.get("similarity", 0))) * 100, 1),
            })
        return {"query": query, "count": len(out), "papers": out}

    # ------------------------------------------------------------ verification
    def verify_text(
        self,
        text: str,
        query: Optional[str] = None,
        corpus_size: int = 15,
    ) -> Dict[str, Any]:
        """Verify the claims in ``text`` against retrieved papers.

        v1 builds the evidence corpus from the abstracts of papers retrieved for
        ``query`` (or for the text itself). Full-text PDF ingestion is a drop-in
        upgrade behind the same retriever interface.
        """
        if not self.verifier:
            return {
                "input_text": text,
                "claims": [],
                "error": "verification backend unavailable (set GEMINI_API_KEY or run Ollama)",
            }

        # Populate the verifier's evidence index from search results, if the
        # service was given a search agent and an index-populating hook.
        if self.search_agent and hasattr(self.verifier, "ingest_papers"):
            papers = self.search_agent.search(query or text, max_results=corpus_size)
            self.verifier.ingest_papers(papers)

        report = self.verifier.verify_text(text)
        return report.to_dict()

    # --------------------------------------------------------------- factories
    @classmethod
    def create_default(cls) -> "ResearchService":
        """Build the real service, degrading gracefully on missing deps."""
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent))

        search_agent = None
        embedder = None
        llm = None
        llm_available = False

        try:
            from agents.search_agent import SearchAgent
            search_agent = SearchAgent()
            embedder = search_agent.embeddings
        except Exception as e:  # pragma: no cover - environment dependent
            print(f"[service] search agent unavailable: {e}")

        # Pick an LLM provider: Gemini if a key is set, else local Mistral.
        try:
            from config import GEMINI_API_KEY
            from verification.providers import GeminiProvider, MistralProvider
            if GEMINI_API_KEY:
                from models.gemini_client import GeminiClient
                llm = GeminiProvider(GeminiClient(GEMINI_API_KEY))
                llm_available = True
            else:
                from models.llm import MistralLLM
                llm = MistralProvider(MistralLLM())
                llm_available = True
        except Exception as e:  # pragma: no cover
            print(f"[service] LLM unavailable: {e}")

        verifier = None
        if embedder is not None and llm is not None:
            try:
                verifier = _build_verifier(embedder, llm)
            except Exception as e:  # pragma: no cover
                print(f"[service] verifier unavailable: {e}")

        return cls(
            search_agent=search_agent,
            verifier=verifier,
            embedder=embedder,
            llm_available=llm_available,
        )


def _build_verifier(embedder, llm):
    """Wire a ClaimVerificationEngine whose evidence comes from paper abstracts.

    Returns an engine with an extra ``ingest_papers`` method so the service can
    refresh the corpus per request.
    """
    from utils.pdf_rag import PaperRAGIndex
    from verification.engine import ClaimVerificationEngine, RAGEvidenceRetriever

    index = PaperRAGIndex(embedder, chunk_size=600, overlap=80)
    retriever = RAGEvidenceRetriever(index)
    engine = ClaimVerificationEngine(retriever, llm, evidence_per_claim=6)

    def ingest_papers(papers):
        for p in papers:
            text = p.get("abstract") or ""
            if not text:
                continue
            index.add_paper(
                paper_id=str(p.get("id") or p.get("title")),
                full_text=text,
                title=p.get("title", ""),
                url=p.get("url", ""),
            )

    engine.ingest_papers = ingest_papers  # type: ignore[attr-defined]
    return engine

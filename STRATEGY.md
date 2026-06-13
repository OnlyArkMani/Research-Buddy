# Research Buddy — Product & Engineering Strategy

*A strategy for turning Research Buddy from a working demo into a project that gets interviews at FAANG and frontier AI labs.*

---

## 1. Where the project actually stands today

I read the whole codebase, not just the README. There's a real distinction between what the README *claims* and what the code *does*, and closing that gap is itself part of the strategy — because in an interview, the gap is exactly where you get caught.

### What genuinely works

The core search-and-rank loop is real and reasonably good:

- **Multi-source retrieval** across arXiv, Semantic Scholar, and PubMed, run in parallel via `asyncio.run_in_executor`. arXiv and Semantic Scholar return clean metadata; Semantic Scholar even returns real citation counts.
- **Deduplication** by normalized title string (`api_clients` → `search_agent._deduplicate`).
- **Semantic embeddings** with `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim) stored in a **FAISS** index.
- **Composite re-ranking**: `relevance * 0.6 + citation_score * 0.3 + recency_score * 0.1`. This is a genuinely sensible scoring idea and worth keeping.
- **Abstract summarization** in three styles (concise / detailed / key-points) via Gemini with a Mistral-7B fallback.
- **Citation generation** in APA / IEEE / MLA / BibTeX.
- **Bookmarks + collections** persisted in SQLite, and a **natural-language filter manager** (regex-based) for year and citation thresholds.
- **Firebase auth + Flask landing page** with JWT sessions, and a Chainlit chat UI.

That's a solid foundation. The retrieval-and-rank skeleton is the hard part and it exists.

### What is claimed but not actually built (the credibility gap)

These are advertised in the README but are missing, stubbed, or dead code:

- **PDF RAG does not exist.** `backend/utils/pdf_rag.py` is an *empty file*. `pdf_processor.py` can download and extract text, but nothing chunks, embeds, indexes, or retrieves over full-text. All summarization runs on the **abstract only**. This is the single biggest gap, because "PDF RAG" is the headline feature.
- **The autonomous agent is never used.** `AutonomousResearchAgent` (a 5-step pipeline) is fully written but is *not wired into the frontend* — `app.py` never calls it. It's orphaned code.
- **The citation graph is never populated.** `CitationGraphVisualizer` builds a NetworkX/Plotly graph, but `add_citations()` is never called with real edges, and the graph isn't rendered in the UI. It's a visualization of nothing.
- **LangChain / LangGraph are in `requirements.txt` but unused.** There is no graph, no agent loop, no tool-calling anywhere in the code.
- **CORE source is a stub** that returns `[]`.
- **PubMed citation counts are always 0**, so any paper from PubMed is structurally penalized by the ranking formula.

### What is actively broken or risky

- **The Gemini model is dead.** `gemini_client.py` calls `GenerativeModel('gemini-pro')`. That model name was retired in 2024; the current API rejects it. **Right now your Gemini path almost certainly throws**, silently falling back or returning empty strings. This needs to move to a current model (e.g. `gemini-2.x-flash`).
- **The FAISS index grows unbounded and is polluted.** Every `search()` call re-embeds results and `.add()`s them to the same index without dedup against what's already there, so the vector store accumulates duplicates across sessions and semantic search quality degrades over time.
- **Intent routing is brittle keyword matching.** `app.py` routes with `if any(word in query for word in [...])`. The substring `"after"` triggers the filter handler; `"on"` is a research keyword. A query like "summarize the trade-offs after 2020" hits the wrong branch. This is the part most worth replacing with a real agent.
- **No tests, no CI, no error budget.** A single malformed API response can break a search with only a broad `try/except` to catch it.

**The honest one-line summary:** Research Buddy today is a competent *semantic search + abstract summarizer with a chat UI*. It is marketed as an *agentic, full-text RAG research platform*. The strategy below is about actually becoming the second thing.

---

## 2. What FAANG / AI-lab hiring managers are actually scanning for

From current (2026) hiring signal research, three things separate portfolio projects that get interviews from the thousands that don't:

1. **It solves a real problem end-to-end** — data in, deployed system out — not a notebook.
2. **It shows production signals** — how you handle failure, evaluate quality, observe behavior in flight, and ship.
3. **RAG and agentic systems are the single most in-demand skill set** right now. A *retrieval-augmented, agentic* system grounded in real data is the most effective single project for getting hired.

The thing almost no junior portfolio has — and the thing that will separate you most — is **evaluation and observability**. Anyone can wire an LLM to a vector DB. Very few can answer "how good is your retrieval, how do you know, and what happens when it regresses?" If you can show numbers (recall@k, nDCG, faithfulness, answer-relevance) and traces, you immediately read as someone who has shipped, not someone who has tutorialed.

> Strategic implication: don't add ten more features. Take the features you have, make them *real*, wrap them in an *agent loop*, and put an *evaluation + observability layer* around the whole thing. Depth and rigor beat breadth.

---

## 3. The strategic repositioning

**Today's pitch:** "An AI chatbot that searches papers and summarizes abstracts."
That sounds like a hackathon project. There are thousands of them.

**The pitch to aim for:** "An agentic literature-review system that plans a research question into sub-queries, retrieves across multiple sources with hybrid search and reranking, reads full papers via RAG, synthesizes a cited literature review, and is continuously evaluated on retrieval and faithfulness metrics with full request tracing."

That second sentence is a *systems* description. It signals retrieval engineering, agent orchestration, evaluation, and ops — the exact competencies AI teams hire for. The underlying domain (academic papers) is the same; the *engineering story* is what changes.

The narrowing decision worth making: **pick "automated literature review" as the flagship capability.** It's a concrete, demoable, genuinely useful task ("Give me a cited review of X with research gaps"), it naturally requires every impressive component (planning, multi-source retrieval, RAG, synthesis, citation), and it's a real pain point for actual researchers. One sharp flagship beats five shallow features.

---

## 4. The feature set that earns the repositioning

Grouped by the engineering competency each one signals. This is the menu to build from — not a timeline.

### A. Real Retrieval Engineering *(signals: search/IR depth)*

- **Hybrid retrieval**: combine dense (embeddings) with sparse **BM25** keyword search, then fuse (reciprocal rank fusion). This is the current production default and a strong talking point.
- **Two-phase retrieval with a reranker**: retrieve top-K cheaply, then rerank with a cross-encoder (BGE-reranker, Jina, or Cohere Rerank) for precision. This is the highest-leverage single quality upgrade in modern RAG.
- **Query expansion / rewriting**: have the LLM decompose a question into sub-queries and rewrite for each source's syntax.
- **Fix the vector store**: dedup before insert, persist with metadata, and support metadata pre-filtering (year, source) at the vector level. Consider moving from raw FAISS to **Qdrant** or **pgvector** for real filtering + persistence.

### B. Actual Full-Text RAG *(signals: the headline skill)*

- **Build `pdf_rag.py` for real**: download → parse (PyMuPDF) → chunk (semantic or recursive) → embed → index per-paper → retrieve relevant chunks → answer with inline citations to page/section.
- **Grounded Q&A over a paper or a set of papers**: "What dataset did paper 3 use?" answered from the actual text, with the source span quoted. This is the difference between "summarizes abstracts" and "reads papers."
- **Cross-paper synthesis**: retrieve across the full-text index of multiple papers to write a grounded comparison.

### C. Agentic Orchestration *(signals: the most in-demand 2026 skill)*

- **Replace keyword routing with a real agent loop in LangGraph** (which you already have as a dependency). Nodes: plan → retrieve → rerank → read → critique → synthesize, with conditional edges.
- **Tool-calling**: expose search, filter, summarize, cite, and PDF-QA as tools the agent selects, instead of brittle `if "cite" in query`.
- **LLM-as-judge critique loop**: after drafting, a critic node scores the answer and can trigger another retrieval round if confidence is low. This "self-correcting RAG" is a strong, current talking point.
- **Wire in the orphaned `AutonomousResearchAgent`** — you've already written most of this; it just needs to become the LangGraph backbone and be connected to the UI.

### D. Evaluation Harness *(signals: the rare, decisive differentiator)*

- **Retrieval metrics**: build a small labeled query set and report **recall@k, MRR, nDCG**. Show that hybrid+rerank beats dense-only with numbers.
- **RAG quality metrics**: use **RAGAS** or a custom LLM-as-judge for **faithfulness, answer relevance, context precision/recall**.
- **A regression suite**: a fixed eval set that runs in CI so a prompt or model change that drops quality is caught. *This is the single most resume-distinguishing component.*
- Put the headline numbers in the README ("hybrid+rerank lifted nDCG@10 from 0.62 → 0.81 on a 50-query benchmark"). Quantified results are what recruiters and engineers remember.

### E. Observability & Ops *(signals: "has shipped real systems")*

- **Tracing** with LangSmith or **Langfuse** (open-source, self-hostable): trace every agent node, retrieval round, token cost, and latency.
- **Dockerize** the whole stack and provide one-command `docker compose up`.
- **CI** (GitHub Actions) running tests + the eval suite on every PR.
- **A metrics/cost dashboard**: tokens, latency, cost per query, cache hit rate.

### F. Genuine real-world utility *(the "solves a real problem" box)*

- **Citation network that's actually populated** (Semantic Scholar exposes references/citations — fetch them, then your existing graph code lights up).
- **Export a finished, cited literature review** to DOCX/PDF (your `export_manager` already does the file-writing part).
- **"What should I read first?" reading-order recommendations** from the citation graph (PageRank is already coded in `citation_graph.py`).
- **Research-gap detection**: explicitly prompt the synthesis step to surface what the literature *hasn't* covered.

---

## 5. Recommended tech stack

Keep what's good (Python, sentence-transformers, the scoring idea). Upgrade the parts that signal seniority.

| Layer | Today | Recommended | Why it matters for the resume |
|---|---|---|---|
| **LLM** | Gemini (`gemini-pro`, dead) + Mistral-7B | Current Gemini (`gemini-2.x-flash`) and/or an OpenAI/Anthropic model, keep local Ollama as offline fallback | Shows you track the fast-moving model landscape; the current code is broken |
| **Orchestration** | `if/elif` keyword routing | **LangGraph** agent with tool-calling + critique loop | "Agentic" is the headline 2026 skill; you already depend on it |
| **Retrieval** | Dense-only (FAISS flat) | **Hybrid** (BM25 + dense) + **cross-encoder reranker** | The current production-default RAG pattern |
| **Vector store** | FAISS file (unbounded, no filtering) | **Qdrant** or **pgvector** | Real metadata filtering + persistence; a named vector DB reads as production |
| **Full-text** | None (abstracts only) | PyMuPDF + chunking + per-paper index | Turns "summarizer" into real **RAG** |
| **Evaluation** | None | **RAGAS** + custom IR metrics + CI regression set | The rare differentiator — most portfolios have zero eval |
| **Observability** | `print()` statements | **Langfuse** or **LangSmith** tracing | Signals "I operate systems, not just build them" |
| **Backend API** | Logic embedded in Chainlit | **FastAPI** service layer | Decouples logic from UI; enables the new frontend; standard production shape |
| **Frontend** | Chainlit | **Next.js / React** (your stated next step) talking to FastAPI | A polished custom UI over a clean API is far more impressive than a framework demo |
| **Packaging** | Manual two-terminal startup | **Docker Compose** + GitHub Actions CI | One-command demo; "deployable" is a hiring signal |

**The decoupling principle that makes the new frontend possible:** move all business logic out of `app.py`/Chainlit and into a **FastAPI** backend. Then Chainlit, a Next.js app, a CLI, or an eval script are all just clients of the same API. This single refactor is what makes your "different frontend" goal clean instead of a rewrite — and a well-designed API boundary is itself a maturity signal.

---

## 6. Sequencing principle (not a dated plan)

When you start coding, order the work by *credibility-per-hour*, roughly:

1. **Stop the bleeding** — fix the dead Gemini model and the polluting FAISS inserts. The demo must not be silently broken.
2. **Carve out the API** — lift logic into FastAPI so everything downstream is clean.
3. **Make RAG real** — build `pdf_rag.py` so the headline claim becomes true.
4. **Add hybrid + reranker** — the biggest quality jump for the least code.
5. **Wrap it in a LangGraph agent** — replace keyword routing; light up the orphaned autonomous agent.
6. **Build the eval harness + tracing** — the differentiators; do these *before* the new frontend so you have numbers to show.
7. **Then the Next.js frontend** — now it's a polished face on a genuinely strong system.

Do the unglamorous middle (4–6) before the visible end (7). The eval numbers and traces are what convert "nice demo" into "this person can do the job."

---

## 7. The interview narrative this unlocks

When an engineer asks "tell me about a project," the strong version sounds like:

> "I built an agentic literature-review system. It plans a research question into sub-queries, retrieves across arXiv, Semantic Scholar, and PubMed with hybrid BM25+dense search, reranks with a cross-encoder, reads the full PDFs via RAG, and synthesizes a cited review with detected research gaps. The whole loop runs in LangGraph with a self-critique node that re-retrieves when faithfulness is low. I evaluate it on a 50-query benchmark — recall@k and nDCG for retrieval, RAGAS faithfulness for generation — and that suite runs in CI so quality regressions get caught. Every request is traced in Langfuse so I can see retrieval rounds, token cost, and latency per query."

Every clause in that paragraph maps to a thing the code actually does. That's the bar. The work above is what makes each clause true.

---

---

## 8. The differentiator MVP: a Claim Verification & Contradiction Engine

This is the one feature that targets a **structural** weakness of frontier models, not just a missing convenience. It's what makes the project memorable.

### The capability

Paste any research claim — or a sentence lifted straight from an LLM's answer — and get back a verdict grounded in real papers: **supported / refuted / contested / insufficient evidence**, where *every* judgment quotes the exact source span and links to the real paper.

### Why frontier models structurally can't do this well (June 2026)

These are not gaps that a bigger model closes; they're properties of how parametric generation works:

1. **They hallucinate the evidence.** Citation hallucination runs **14–95% across vendors**, and **3–13% of URLs stay fabricated even with web search + RAG**. A generative model cannot guarantee a cited span exists or says what it claims. This engine never asserts anything it can't quote from a retrieved passage.
2. **They smooth disagreement into false consensus.** Ask "does X cause Y?" and you get one confident answer; the literature is often split. This engine returns a consensus distribution (e.g. "7 support / 3 refute / 2 neutral") with the dissenting papers shown.
3. **Their knowledge is stale.** They don't know the newest papers or which were **retracted**, and will cite retracted work. This retrieves live and flags retractions/low-credibility venues.
4. **They don't abstain.** With thin evidence they confabulate. This returns a calibrated "insufficient evidence" — abstention is a designed feature.

### The killer demo

Take a confident answer from ChatGPT or Gemini, run each claim through the verifier, and highlight which sentences are unsupported, mis-cited, or contradicted by the literature. The positioning: **the fact-checking / grounding layer that frontier models lack.**

### Engineering components (all resume-strong)

- **Claim decomposition**: split a paragraph into atomic, checkable claims.
- **Span-level retrieval**: full-text RAG returning candidate evidence passages (reuses the hybrid+rerank stack from §4–5).
- **Stance / NLI classification**: per passage, classify *supports / refutes / neutral* relative to the claim (fine-tuned NLI model or LLM-as-classifier with span grounding).
- **Evidence aggregation with calibrated confidence + abstention**: combine per-passage stances into a verdict and a confidence the system is actually calibrated on (a real ML talking point).
- **Retraction & credibility checks**: cross-reference retraction databases / venue signals.
- **Verifiable output**: an evidence table where every row is a real, clickable, quoted span.

### Honest framing for interviews

Don't claim "impossible for an LLM." Claim the accurate, still-impressive thing: reliable, span-grounded, contradiction-aware verification **with abstention** is an *architecture* (a verification pipeline with retrieval, NLI, calibration, and freshness) — not something parametric weights provide. That distinction is exactly the kind of systems thinking AI teams hire for.

### Why it fits

It's additive, not a detour: it consumes the same retrieval/RAG infrastructure the rest of the strategy builds, and it slots cleanly into the LangGraph agent as a `verify` tool/node. The eval story is also natural — you can benchmark verification accuracy against a labeled claim set (precision/recall on supports-vs-refutes, calibration error on confidence).

---

*Built from a full read of the current codebase (Nov 2025 state) and 2026 AI-hiring signal + frontier-model-limitation research. Sources are in the chat messages accompanying this document.*

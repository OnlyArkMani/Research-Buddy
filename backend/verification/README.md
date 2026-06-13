# Claim Verification & Contradiction Engine

The differentiator feature (see `../../STRATEGY.md` §8). Takes a research claim —
or any sentence from an LLM's answer — and returns a verdict grounded in real
papers, where **every judgment quotes the exact source span**.

## Why it matters

Frontier models hallucinate citations (14–95% across vendors), smooth
disagreement into false consensus, and never abstain. This engine:

- **asserts nothing it can't quote** — a supports/refutes verdict is dropped to
  neutral unless its quote is actually grounded in the retrieved passage
  (`stance_classifier._quote_grounded`);
- **surfaces contradiction** — returns `CONTESTED` when the literature is split
  instead of picking a side;
- **abstains** — returns `INSUFFICIENT` when credible, confident evidence is thin;
- **discounts bad sources** — retracted papers contribute zero weight to a verdict.

## Pipeline

```
text --extract_claims--> [atomic claims]
   each claim --retrieve--> [evidence passages]   (full-text RAG, utils/pdf_rag.py)
            --classify_stance--> [supports/refutes/neutral + grounded quote]
                     --aggregate--> Verdict + calibrated confidence + consensus
```

Every stage is injected (`LLMProvider`, `EvidenceRetriever`, embedder), so the
whole thing runs against Gemini, local Mistral, or a scripted mock in tests.

## Modules

| File | Role |
|---|---|
| `schema.py` | Dataclasses/enums: `Claim`, `EvidencePassage`, `StanceJudgment`, `Verdict`, reports |
| `providers.py` | `LLMProvider` protocol + Gemini/Mistral adapters + `MockLLMProvider` |
| `claim_extractor.py` | Decompose text into atomic claims (LLM + sentence fallback) |
| `stance_classifier.py` | NLI stance per (claim, passage) with the anti-hallucination grounding guard |
| `aggregator.py` | Pure decision core: verdict + confidence + abstention + contradiction |
| `engine.py` | Orchestrator + `RAGEvidenceRetriever` + markdown report formatter |

## Try it

```bash
python verify_demo.py            # end-to-end demo, no API keys / no downloads
python /tmp/run_rb.py            # or run the tests/ suite (16 tests)
```

## Production wiring (next steps)

- Swap `MockLLMProvider` for `GeminiProvider(GeminiClient(...))` and the
  `ToyEmbedder` for the project's `EmbeddingModel`.
- Feed `RAGEvidenceRetriever` a `PaperRAGIndex` populated from real PDFs via
  `utils/pdf_processor.PDFProcessor`.
- Add a retraction checker / venue-credibility function (the hooks are already
  parameters on `RAGEvidenceRetriever`).
- Benchmark stance accuracy + confidence calibration on a labelled claim set.

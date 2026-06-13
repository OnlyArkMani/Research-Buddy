"""FastAPI service for Research Buddy.

Thin HTTP layer over ``ResearchService`` (all logic lives there). This is what
the React frontend talks to, and what decouples the app from any single UI.

Run:
    uvicorn backend.api:app --reload --port 8000
or:
    python backend/api.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from service import ResearchService

app = FastAPI(
    title="Research Buddy API",
    version="1.0.0",
    description="Agentic literature search + claim verification.",
)

# Allow the Vite dev server (and common local ports) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the service once at startup. Degrades gracefully if deps are missing.
_service: Optional[ResearchService] = None


def get_service() -> ResearchService:
    global _service
    if _service is None:
        _service = ResearchService.create_default()
    return _service


# ------------------------------------------------------------------- schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural-language search query")
    max_results: int = Field(20, ge=1, le=50)


class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=3, description="A claim, or an LLM answer to fact-check")
    query: Optional[str] = Field(
        None, description="Optional search query to build the evidence corpus; defaults to the text"
    )
    corpus_size: int = Field(15, ge=1, le=50)


# -------------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    svc = get_service()
    return {
        "status": "ok",
        "search_available": svc.search_agent is not None,
        "verification_available": svc.verifier is not None,
        "llm_available": svc.llm_available,
    }


@app.post("/api/search")
def search(req: SearchRequest):
    return get_service().search(req.query, max_results=req.max_results)


@app.post("/api/verify")
def verify(req: VerifyRequest):
    return get_service().verify_text(req.text, query=req.query, corpus_size=req.corpus_size)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

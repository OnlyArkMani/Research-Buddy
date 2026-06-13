# Research Buddy — React Frontend

A Vite + React UI for Research Buddy. It talks to the FastAPI backend
(`backend/api.py`) and showcases the **Claim Verifier**: paste a claim or an AI
answer, and each atomic claim gets a colour-coded verdict (Supported / Refuted /
Contested / Insufficient) backed by quoted source spans.

## Run the full stack (two terminals)

### 1. Backend (FastAPI)

```bash
# from the repo root
pip install -r backend/requirements.txt        # first time
# optional: set a key so the LLM-dependent verifier turns on
#   Windows:  set GEMINI_API_KEY=your_key
#   macOS/Linux: export GEMINI_API_KEY=your_key
uvicorn backend.api:app --reload --port 8000
```

Check it's up: open http://localhost:8000/api/health — you should see
`{"status":"ok", ...}`. The flags tell you what's available:
`search_available`, `verification_available`, `llm_available`.

> The backend degrades gracefully: with no `GEMINI_API_KEY` it tries local
> Mistral via Ollama; with neither, search still works and `/api/verify`
> returns a clear "verification backend unavailable" message instead of crashing.

### 2. Frontend (Vite dev server)

```bash
cd frontend-react
npm install        # first time
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api/*` to
`http://localhost:8000` (see `vite.config.js`), so there's no CORS setup needed.

## Build for production

```bash
cd frontend-react
npm run build      # outputs static files to dist/
npm run preview    # serve the built app locally
```

## How it maps to the backend

| UI action | Endpoint | Service method |
|---|---|---|
| Verify a claim | `POST /api/verify` | `ResearchService.verify_text` |
| Search papers | `POST /api/search` | `ResearchService.search` |
| Status badge | `GET /api/health` | — |

All logic lives in `backend/service.py`; the API and this frontend are thin
clients over it.

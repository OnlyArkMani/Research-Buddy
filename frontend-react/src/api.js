// Tiny API client for the FastAPI backend. Uses relative URLs so the Vite dev
// proxy (see vite.config.js) forwards /api/* to http://localhost:8000.

async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`);
  }
  return res.json();
}

export function getHealth() {
  return fetch("/api/health").then((r) => r.json());
}

export function searchPapers(query, maxResults = 20) {
  return post("/api/search", { query, max_results: maxResults });
}

export function verifyText(text, query = null, corpusSize = 15) {
  return post("/api/verify", { text, query, corpus_size: corpusSize });
}

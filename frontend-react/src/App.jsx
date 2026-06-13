import { useEffect, useState } from "react";
import { getHealth, searchPapers, verifyText } from "./api.js";

const VERDICT_META = {
  supported: { label: "Supported", className: "v-supported", icon: "✓" },
  refuted: { label: "Refuted", className: "v-refuted", icon: "✕" },
  contested: { label: "Contested", className: "v-contested", icon: "⚖" },
  insufficient: { label: "Insufficient evidence", className: "v-insufficient", icon: "?" },
};

export default function App() {
  const [tab, setTab] = useState("verify");
  const [health, setHealth] = useState(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "down" }));
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="logo">🔬</span>
          <div>
            <h1>Research Buddy</h1>
            <p className="tagline">Agentic literature search &amp; claim verification</p>
          </div>
        </div>
        <HealthBadge health={health} />
      </header>

      <nav className="tabs">
        <button className={tab === "verify" ? "active" : ""} onClick={() => setTab("verify")}>
          Verify a claim
        </button>
        <button className={tab === "search" ? "active" : ""} onClick={() => setTab("search")}>
          Search papers
        </button>
      </nav>

      <main className="main">{tab === "verify" ? <VerifyPanel /> : <SearchPanel />}</main>

      <footer className="footer">
        Grounded answers only — every verdict is backed by a quoted source span, or it abstains.
      </footer>
    </div>
  );
}

function HealthBadge({ health }) {
  if (!health) return <span className="health checking">connecting…</span>;
  if (health.status !== "ok")
    return <span className="health down">API offline</span>;
  return (
    <span className="health ok" title={`LLM: ${health.llm_available ? "on" : "off"}`}>
      API online{health.verification_available ? "" : " (verifier offline)"}
    </span>
  );
}

/* ----------------------------- Verify panel ----------------------------- */

function VerifyPanel() {
  const [text, setText] = useState(
    "Dropout reduces overfitting in deep neural networks, and it also speeds up training."
  );
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

  async function onVerify() {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await verifyText(text, query.trim() || null);
      if (res.error) setError(res.error);
      else setReport(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <p className="hint">
        Paste a research claim — or a sentence from an AI answer — and it is decomposed into
        atomic claims and checked against retrieved papers. The system surfaces contradictions and
        abstains when evidence is thin, instead of guessing.
      </p>

      <label className="field-label">Text to verify</label>
      <textarea
        className="textarea"
        rows={4}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. Transformers outperform RNNs on machine translation."
      />

      <div className="row">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Optional: search query for evidence (defaults to the text)"
        />
        <button className="primary" onClick={onVerify} disabled={loading || text.trim().length < 3}>
          {loading ? "Verifying…" : "Verify"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {report && (
        <div className="results">
          {report.claims.length === 0 && <p className="hint">No checkable claims found.</p>}
          {report.claims.map((c, i) => (
            <ClaimCard key={i} claim={c} />
          ))}
        </div>
      )}
    </section>
  );
}

function ClaimCard({ claim }) {
  const meta = VERDICT_META[claim.verdict] || VERDICT_META.insufficient;
  const evidence = (claim.evidence || []).filter((e) => e.label !== "neutral");
  return (
    <article className={`claim-card ${meta.className}`}>
      <div className="claim-head">
        <span className={`verdict-pill ${meta.className}`}>
          {meta.icon} {meta.label}
        </span>
        <span className="confidence">{Math.round((claim.confidence || 0) * 100)}% confidence</span>
      </div>
      <p className="claim-text">{claim.claim}</p>

      <div className="consensus">
        <span className="c-support">{claim.consensus.supports} support</span>
        <span className="c-refute">{claim.consensus.refutes} refute</span>
        <span className="c-neutral">{claim.consensus.neutral} neutral</span>
      </div>

      {claim.flags && claim.flags.map((f, i) => <div key={i} className="flag">⚠ {f}</div>)}

      {evidence.length > 0 ? (
        <ul className="evidence">
          {evidence.map((e, i) => (
            <li key={i} className={e.label === "supports" ? "ev-support" : "ev-refute"}>
              <span className="ev-tag">{e.label === "supports" ? "supports" : "refutes"}</span>
              <span className="ev-conf">{Math.round((e.confidence || 0) * 100)}%</span>
              {e.retracted && <span className="ev-retracted">RETRACTED</span>}
              <blockquote>“{e.quote}”</blockquote>
              <cite>
                {e.url ? (
                  <a href={e.url} target="_blank" rel="noreferrer">
                    {e.locator}
                  </a>
                ) : (
                  e.locator
                )}
              </cite>
            </li>
          ))}
        </ul>
      ) : (
        <p className="hint">No passage directly addressed this claim.</p>
      )}
    </article>
  );
}

/* ----------------------------- Search panel ----------------------------- */

function SearchPanel() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [papers, setPapers] = useState(null);

  async function onSearch() {
    setLoading(true);
    setError(null);
    setPapers(null);
    try {
      const res = await searchPapers(query);
      if (res.error) setError(res.error);
      else setPapers(res.papers);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <p className="hint">Search arXiv, Semantic Scholar and PubMed, ranked by relevance, citations and recency.</p>
      <div className="row">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && query.trim() && onSearch()}
          placeholder="e.g. contrastive learning for medical imaging"
        />
        <button className="primary" onClick={onSearch} disabled={loading || query.trim().length < 2}>
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {papers && (
        <div className="results">
          {papers.length === 0 && <p className="hint">No papers found.</p>}
          {papers.map((p, i) => (
            <article key={i} className="paper-card">
              <h3>
                {p.url ? (
                  <a href={p.url} target="_blank" rel="noreferrer">
                    {p.title}
                  </a>
                ) : (
                  p.title
                )}
              </h3>
              <div className="paper-meta">
                <span>{p.authors}</span>
                <span>{p.year}</span>
                <span>{p.citations} citations</span>
                <span>{p.source}</span>
                <span className="rel">{p.relevance}% match</span>
              </div>
              {p.abstract && <p className="abstract">{p.abstract.slice(0, 320)}…</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

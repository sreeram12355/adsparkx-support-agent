# 🎧 Persona-Adaptive Customer Support Agent (CloudDesk)

An AI-powered customer-support agent that **detects the customer's persona**,
**retrieves grounded answers from a knowledge base (RAG)**, **adapts its tone**
to the persona, and **escalates to a human** with a structured handoff summary
when it cannot (or should not) resolve the issue itself.

Built for the AdSparkx AI assignment. Domain: a fictional SaaS product, **CloudDesk**.

---

## 1. Project Overview

The agent supports three personas and changes both *what* it retrieves and *how*
it answers:

| Persona | How it's detected | Response style |
|---------|-------------------|----------------|
| 🛠️ **Technical Expert** | Technical terms, error codes, APIs, logs | Detailed, root-cause analysis, step-by-step |
| 😤 **Frustrated User** | Emotional/urgent language, complaints, `!!!` | Empathetic, simple, reassuring, action-oriented |
| 📈 **Business Executive** | Outcome/impact/timeline language | Concise, impact-focused, minimal jargon, ETA |

Every response is **grounded only in retrieved knowledge-base content** — the
model is instructed not to invent information, and when the KB has no answer the
agent escalates instead of hallucinating.

---

## 2. Tech Stack

| Layer | Choice | Version |
|-------|--------|---------|
| Language | Python | 3.11+ |
| LLM | OpenAI GPT (`gpt-4o`, configurable) | `openai>=1.40` |
| Embeddings | Sentence-Transformers `all-MiniLM-L6-v2` (local, offline) | `sentence-transformers>=3.0` |
| Vector DB | FAISS (`IndexFlatIP`, cosine) | `faiss-cpu>=1.8` |
| Doc loading | `pypdf`, `python-docx` | — |
| PDF generation (sample KB) | ReportLab | `reportlab>=4.2` |
| UI | CLI + Streamlit | `streamlit>=1.36` |
| Config | `python-dotenv` | `>=1.0` |

> **Why local embeddings?** No API cost, fully offline ingestion, and retrieval
> still works even when the OpenAI quota is exhausted. Only generation/persona
> detection require the OpenAI key.

---

## 3. Architecture

```
                ┌──────────────────────────────────────────────────────────┐
   User Query ─▶│  1. PERSONA DETECTION   (rule-based signal + LLM judge)    │
                │     → persona, confidence, sentiment                       │
                └───────────────┬──────────────────────────────────────────┘
                                ▼
                ┌──────────────────────────────────────────────────────────┐
                │  2. RETRIEVAL (RAG)     embed query → FAISS top-k          │
                │     → chunks + cosine scores + source/page metadata        │
                └───────────────┬──────────────────────────────────────────┘
                                ▼
                ┌──────────────────────────────────────────────────────────┐
                │  3. ESCALATION CHECK   (configurable triggers)             │
                │     low score? sensitive? repeated dissatisfaction? human? │
                └───────┬───────────────────────────────────┬──────────────┘
                  no    ▼                              yes   ▼
       ┌────────────────────────────┐      ┌────────────────────────────────┐
       │ 4. RESPONSE GENERATION      │      │ 5. HUMAN HANDOFF                │
       │   persona-adapted + grounded│      │   structured summary (JSON):    │
       │   answer with citations     │      │   persona, issue, docs used,    │
       └────────────────────────────┘      │   attempted steps, history,     │
                                            │   recommended next steps        │
                                            └────────────────────────────────┘
```

Code map:

```
persona-support-agent/
├── data/                      # Knowledge base (18 docs incl. 2 PDFs)
├── scripts/generate_pdfs.py   # Builds the sample PDF policies
├── src/
│   ├── config.py              # All tunable settings + escalation rules
│   ├── personas.py            # Persona defs, keyword rules, response styles
│   ├── embeddings.py          # Cached local embedding model
│   ├── ingest.py              # load → chunk → embed → FAISS (with metadata)
│   ├── retriever.py           # top-k cosine retrieval
│   ├── llm.py                 # OpenAI: persona detection + grounded generation
│   ├── escalation.py          # Escalation triggers + handoff summary builder
│   └── agent.py               # Orchestrator + multi-turn memory
├── cli.py                     # Interactive command-line chatbot
├── app.py                     # Streamlit chat UI (bonus)
├── requirements.txt
└── .env.example
```

---

## 4. Persona Detection Strategy

**Hybrid classification** (rules + LLM):

1. **Rule-based signal** (`personas.py → rule_based_scores`): each persona has a
   keyword list. We count hits; for the Frustrated User we also count `!` and
   ALL-CAPS shouting. This is deterministic, instant, and works offline.
2. **LLM judge** (`llm.py → detect_persona`): GPT receives the message, the
   recent conversation, the three persona descriptions, **and the rule-based
   hit counts as a hint**, then returns strict JSON:
   `{persona, confidence, sentiment, reason}` (temperature 0, JSON mode).
3. **Fallback:** if the LLM call fails, we use the rule-based best guess so the
   system degrades gracefully.

**Prompt design:** the classifier prompt pins the output to the exact three
persona names, asks for a sentiment score (−1…1, reused for escalation), and
forbids free-form output. Invalid labels are coerced to the rule-based guess.

---

## 5. RAG Pipeline Design

- **Chunking:** documents are first split by **section** (Markdown/DOCX headings)
  or **page** (PDF), then by a character splitter (`~700` chars, `120` overlap)
  that prefers paragraph → sentence → word boundaries. This keeps the **section
  name / page number** attached to every chunk.
- **Metadata per chunk:** `source` (file name) + `section` (heading) or `page`
  (PDF page number). Surfaced in the UI as citations like
  `refund_policy.pdf (p.1)` or `api_authentication.md — Common authentication errors`.
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fast,
  strong for short support text), run locally.
- **Vector DB:** FAISS `IndexFlatIP` over **L2-normalised** vectors, so inner
  product equals **cosine similarity**. Exact search — ideal at this corpus size.
- **Retrieval strategy:** embed the query, take **top-k = 4**, keep only chunks
  with cosine ≥ `MIN_RETRIEVAL_SCORE` (default `0.30`) as context. The best score
  doubles as the **confidence signal** for escalation.

Rebuild the index any time with `python -m src.ingest`.

---

## 6. Escalation Logic

All triggers live in `config.py` and are **configurable** via `.env`:

| # | Trigger | Control |
|---|---------|---------|
| 1 | **No relevant docs** found | — |
| 2 | **Low retrieval confidence** (best cosine < threshold) | `MIN_RETRIEVAL_SCORE` (0.30) |
| 3 | **Sustained dissatisfaction** over N turns | `MAX_DISSATISFACTION_TURNS` (2) |
| 4 | **Account-sensitive** topic (billing/legal/account) | `sensitive_keywords` list |
| 5 | **Explicit human request** | `human_request_keywords` list |

Dissatisfaction is tracked across turns using the per-turn **sentiment** score and
the Frustrated-User persona; a positive turn relaxes the counter.

When any trigger fires, the agent stops answering, returns a persona-appropriate
escalation message, and emits a **structured handoff summary**:

```json
{
  "persona": "Frustrated User",
  "issue": "Unable to reset password after multiple attempts",
  "escalation_reasons": ["User dissatisfied across 2 interactions."],
  "documents_used": ["password_reset_guide.md", "troubleshooting_login_issues.md"],
  "attempted_steps": ["Resetting your password", "Common problems"],
  "conversation_history": [ ... ],
  "recommendation": "Self-service has not resolved the issue; assign a human agent to take ownership and follow up directly."
}
```

---

## 7. Setup Instructions

> Requires **Python 3.11+**.

```bash
# 1. Clone and enter
git clone <your-repo-url>
cd persona-support-agent

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env          # Windows: copy .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...

# 5. (Optional) regenerate the sample PDFs — already committed under /data
python scripts/generate_pdfs.py

# 6. Build the vector index from /data
python -m src.ingest

# 7a. Run the CLI
python cli.py

# 7b. OR run the web UI
streamlit run app.py
```

The first run downloads the embedding model (~90 MB) once.

---

## 8. Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI key for persona detection + generation |
| `OPENAI_MODEL` | ❌ | `gpt-4o` | Chat model |
| `EMBEDDING_MODEL` | ❌ | `all-MiniLM-L6-v2` | Local embedding model |
| `TOP_K` | ❌ | `4` | Chunks retrieved per query |
| `MIN_RETRIEVAL_SCORE` | ❌ | `0.30` | Relevance / escalation threshold |
| `MAX_DISSATISFACTION_TURNS` | ❌ | `2` | Dissatisfied turns before escalation |

`.env` is git-ignored — **never commit your key.**

---

## 9. Example Queries

| # | Query | Expected behaviour |
|---|-------|--------------------|
| 1 | *"Can you explain the API authentication failure and provide the exact error codes?"* | **Technical Expert** → detailed answer from `api_authentication.md` with 401/403/429 codes |
| 2 | *"I've tried everything and NOTHING works! I still can't log in!!!"* | **Frustrated User** → empathetic, simple login-troubleshooting steps |
| 3 | *"How does this outage impact our operations and when will it be resolved?"* | **Business Executive** → concise impact + SLA resolution path |
| 4 | *"I was charged twice and want a refund."* | **Escalation** (account-sensitive: billing/refund) + handoff summary |
| 5 | *"How do I set up SAML SSO with Okta and map the email attribute?"* | **Technical Expert** → step-by-step from `sso_saml_configuration.md` |
| 6 | *"What's the secret recipe for your founder's coffee?"* | **Escalation** (no relevant docs / low confidence) — no hallucination |

---

## 10. Bonus Features Implemented

- ✅ **Sentiment analysis** (per-turn score, feeds escalation)
- ✅ **Multi-turn conversation memory** (history threaded into detection + answers)
- ✅ **Confidence scoring** (retrieval cosine scores + persona confidence shown in UI)
- ✅ **Streamlit UI** in addition to the required CLI
- ✅ **Human-in-the-loop** structured handoff packet

---

## 11. Known Limitations & Future Improvements

- **Retrieval is lexical-semantic only** — no re-ranker; a cross-encoder reranker
  would sharpen top-k ordering on ambiguous queries.
- **Persona can shift mid-conversation**; we classify per message (with history
  context) rather than locking a session persona.
- **`attempted_steps`** in the handoff are derived from KB sections surfaced to
  the user, not from confirmed user actions — a confirmation step could make this
  precise.
- **Single-workspace, in-memory sessions** — no persistent storage of
  conversations (SQLite/Redis would enable analytics and resumed sessions).
- **Threshold tuning** — `MIN_RETRIEVAL_SCORE` is set for `all-MiniLM-L6-v2`;
  swapping the embedding model would require re-tuning.

---

## License

Provided for the AdSparkx AI assignment / educational use.

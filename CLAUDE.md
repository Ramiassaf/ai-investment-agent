# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

An AI-powered investment research agent for **gold and silver markets**. It ingests financial news from RSS feeds, a direct scraper, and NewsAPI; filters and embeds articles; then answers natural-language market questions with structured, evidence-backed analysis.

This is **not** a trading bot or financial advisor — it produces market research summaries only.

---

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest fresh articles (run before asking questions)
python -m app.refresh_news

# Start the FastAPI server
uvicorn app.main:app --reload

# Start the Streamlit UI
streamlit run app/streamlit_app.py

# Run a manual end-to-end test (all manual tests follow this pattern)
python app/manual_tests/test_answer.py

# Ask a question directly from Python
from src.llm.answer import answer_question
answer_question("What is driving gold prices right now?")
```

There is no automated test suite — tests in `app/manual_tests/` are standalone scripts run directly with Python.

---

## Environment

File: `.env` (never commit)
```
OPENAI_API_KEY=<your key>
OPENAI_MODEL=gpt-4o-mini
NEWSAPI_KEY=<your key>
```

`OPENAI_MODEL` is resolved lazily in `src/llm/client.py` — raises `ValueError` if unset. Embedding model is `text-embedding-3-small`, hardcoded in `src/retrieval/semantic_retriever.py`.

---

## Architecture: end-to-end pipeline

```
refresh_news.py
    → RSS feeds + FXStreet scraper + NewsAPI
    → ArticleRecord objects
    → data/processed/articles.jsonl (append-only, deduped by article_id)

answer_question(question, domain_articles=None, embeddings=None)

  Streamlit path (pre-cached):
    → domain_articles + embeddings passed in from @st.cache_resource

  FastAPI path (fresh compute):
    → load_articles_jsonl()
    → filter_by_recency(days=30)
    → filter_domain_relevant_articles()
    → prepare_retrieval_corpus() + embed_texts()

  Both paths continue here:
    → semantic_search(top_k=5)       ← deduplicates by URL before returning
    → make_evidence_card() per hit   ← uses classify_driver()[0] (top driver only)
    → aggregate_driver_signals()     ← loops ALL drivers per article (multi-label, weighted by score)
    → summarize_driver_impact()      ← appends signals proportionally using range(count)
    → compute_market_bias() for gold and silver
    → format_driver_summary()
    → build_prompt() with gold_bias + silver_bias
    → generate_answer()
    → structured answer printed + returned
```

### Two execution paths

`answer_question` accepts optional `domain_articles` and `embeddings`. When both are provided (Streamlit), it skips loading/filtering/embedding — those are cached via `@st.cache_resource` at app startup. When called without them (FastAPI, manual tests), it computes fresh each time.

> **Note:** The FastAPI `AskRequest` accepts a `days` field but it is not currently forwarded into `answer_question` — recency is hardcoded to 30 days inside the function.

---

## Key data structures

### `ArticleRecord` (dataclass in `src/storage/article_store.py`)
```python
article_id: str        # sha256[:24] of URL
source: str            # e.g. "FedMonetary", "FXStreetGold"
title: str
url: str
published_date: Optional[str]   # ISO-8601 or RFC-2822
retrieved_at: str      # UTC ISO-8601
raw_text: str
clean_text: str        # same as raw_text currently
tags: list[str]        # e.g. ["gold", "fxstreet"]
```

### Evidence card (dict passed to the prompt)
```python
{ "title", "source", "published_date", "url", "driver", "driver_score", "snippet" }
# snippet = clean_text[:220], driver = top driver only
```

---

## Domain filter logic (`src/retrieval/domain_filter.py`)

Seven signal groups: `direct_metals`, `rates_yields`, `inflation`, `usd`, `risk_geopolitics`, `central_banks`, `supply_demand`.

- Pass immediately if `direct_metals` matches.
- Pass if ≥ 2 non-direct groups match.
- Otherwise rejected.

---

## Driver classification (`src/domain/classify.py`, `src/domain/drivers.py`)

**Multi-label** keyword scoring. Returns all drivers scoring ≥ `SCORE_THRESHOLD=2`, sorted descending. Falls back to `[("OTHER", 0)]`. Used in two places:

- `aggregate_driver_signals` — loops ALL drivers per article, weighted by score
- `evidence.py` — uses only `classify_driver(article)[0]` (top driver) for the evidence card

Driver name map (raw → canonical used in bias computation):
```
RATES_REAL_YIELDS    → rates
USD_DOLLAR           → usd
INFLATION            → inflation
RISK_SENTIMENT       → risk
GEOPOLITICS          → risk
CENTRAL_BANKS        → central_banks
SUPPLY_DEMAND_METALS → supply_demand
```

---

## FastAPI layer (`app/main.py`)

- `GET /health` — `{"status": "ok"}`
- `POST /ask` — `{"question": str, "days": int = 30}` → `{"question", "answer", "gold_bias", "silver_bias"}`

---

## Streamlit UI (`app/streamlit_app.py`)

- `@st.cache_resource` on `load_and_embed_articles()` — loads, filters, and embeds articles once at startup; passes results into `answer_question` to avoid re-embedding on every question.
- Colored bias cards: 🟢 supportive · 🔴 negative · 🟡 mixed · ⬜ unclear
- `sys.path.insert` at top to resolve `src/` imports from the `app/` subdirectory.

---

## Deployment (Render)

The project is live on Render with two separate services, each built from its own Dockerfile:

| Service | Dockerfile | Port | Start command |
|---|---|---|---|
| FastAPI API | `Dockerfile.api` | 8000 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Streamlit UI | `Dockerfile.ui` | 8501 | `streamlit run app/streamlit_app.py --server.address=0.0.0.0 --server.port=8501` |

Both images copy `src/`, `app/`, and `data/` into `/app`. Environment variables (`OPENAI_API_KEY`, `OPENAI_MODEL`, `NEWSAPI_KEY`) must be set in the Render service dashboard — they are not baked into the image.

`data/processed/articles.jsonl` is bundled into the image at build time (snapshot). To refresh articles on Render, the image must be rebuilt and redeployed.

---

## Known architectural limitations

1. `SCORE_THRESHOLD=2` hardcoded in `classify.py` — may need tuning as corpus grows.
2. NewsAPI free tier — limited daily calls, `pageSize=10` per query.
3. Evidence card shows only top driver — multi-label classification is not yet reflected in evidence display.
4. No scheduled ingestion — `refresh_news.py` must be run manually.
5. `days` parameter accepted by FastAPI `/ask` but not passed through to `answer_question`.


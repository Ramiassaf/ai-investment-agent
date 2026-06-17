# AI Investment Agent — Project Reference

## What this project is

An AI-powered investment research agent focused on **gold and silver markets**. It ingests financial news from RSS feeds and direct scrapers, filters and embeds the articles, then answers natural-language market questions with structured, evidence-backed analysis.

This is **not** a trading bot or financial advisor — it produces market research summaries only.

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

---

## File map

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app — `/health` and `/ask` endpoints |
| `app/streamlit_app.py` | Streamlit UI — question input, bias cards, analysis display |
| `app/refresh_news.py` | Entry point to ingest fresh articles from all sources |
| `src/storage/article_store.py` | `ArticleRecord` dataclass, JSONL load/save/dedup, recency filter |
| `src/ingestion/rss_fetcher.py` | Generic RSS fetcher (feedparser + requests, HTML guard) |
| `src/ingestion/rss_to_record.py` | Converts feedparser entries → `ArticleRecord` |
| `src/ingestion/fxstreet_metals_fetcher.py` | Scrapes FXStreet gold/silver pages directly via BeautifulSoup |
| `src/ingestion/newsapi_fetcher.py` | Fetches articles from NewsAPI.org across 6 gold/silver query themes |
| `src/retrieval/domain_filter.py` | Keyword-based domain relevance filter (7 signal groups) |
| `src/retrieval/semantic_retriever.py` | OpenAI embeddings, cosine similarity, URL dedup, semantic search |
| `src/domain/classify.py` | Multi-label driver classification, SCORE_THRESHOLD=2 |
| `src/domain/drivers.py` | Driver → keyword lists (`GOLD_SILVER_DRIVERS`) |
| `src/domain/driver_reasoning.py` | Aggregates driver signals, computes bias, formats for prompt |
| `src/domain/evidence.py` | Builds evidence card dict from `ArticleRecord` |
| `src/llm/client.py` | Thin wrapper around `openai.chat.completions.create` |
| `src/llm/prompts.py` | `SYSTEM_PROMPT` constant + `build_prompt()` |
| `src/llm/answer.py` | Orchestrates the full pipeline: load → filter → embed → answer |

---

## Key data structures

### `ArticleRecord` (dataclass)
```python
article_id: str        # sha256[:24] of URL (or source+title+date fallback)
source: str            # feed name, e.g. "FedMonetary", "FXStreetGold"
title: str
url: str
published_date: Optional[str]   # ISO-8601 or RFC-2822
retrieved_at: str      # UTC ISO-8601
raw_text: str
clean_text: str        # same as raw_text currently; future: full article fetch
tags: list[str]        # e.g. ["gold", "fxstreet"]
```

### Evidence card (dict, passed to prompt)
```python
{
  "title", "source", "published_date", "url",
  "driver", "driver_score",
  "snippet"   # clean_text[:220]
}
```

---

## Domain filter logic (`domain_filter.py`)

Seven signal groups: `direct_metals`, `rates_yields`, `inflation`, `usd`, `risk_geopolitics`, `central_banks`, `supply_demand`.

- **Pass immediately** if `direct_metals` group matches.
- **Pass** if ≥ 2 non-direct groups match.
- Otherwise rejected.

---

## Driver classification (`classify.py`, `drivers.py`)

**Multi-label** keyword scoring. Returns all drivers scoring ≥ `SCORE_THRESHOLD=2`, sorted descending. Falls back to `[("OTHER", 0)]`.

Driver name map (raw → canonical):
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

## Ingestion sources (`app/refresh_news.py`)

| Name | Type | Coverage |
|---|---|---|
| FedMonetary | RSS | Fed monetary policy |
| InvestingCommoditiesNews | RSS | Commodities broadly |
| GoldBroker | RSS | Direct metals news |
| FXStreetGold | Scraper | Gold direct |
| FXStreetSilver | Scraper | Silver direct |
| NewsAPI | API | Geopolitics, risk, USD, central banks, recession, industrial silver |

---

## Environment / config

File: `.env` (never commit)
```
OPENAI_API_KEY=<your key>
OPENAI_MODEL=gpt-4o-mini
NEWSAPI_KEY=<your key>
```

Model is resolved at call time in `client.py` — raises `ValueError` if unset.
Embedding model: `text-embedding-3-small` (hardcoded in `semantic_retriever.py`).

---

## Data storage

- Articles stored at `data/processed/articles.jsonl` (append-only JSONL).
- Deduplication is by `article_id` on every save via `save_articles_jsonl_dedup()`.
- Bad lines in the JSONL are skipped with a printed warning (line number + error).

---

## Known issues fixed

1. `prepare_retrieval_corpus` had variable shadowing bug — fixed.
2. `generate_answer` model default now resolved lazily with clear error if missing.
3. `domain_filter` dict key fixed from `"is relevant"` to `"is_relevant"`.
4. `answer_question` guards added for empty pipeline stages.
5. `load_articles_jsonl` now logs bad lines instead of silently swallowing.
6. `compute_market_bias` wired into pipeline — explicit gold/silver bias computed.
7. `build_prompt` updated — accepts `gold_bias` and `silver_bias` as explicit params.
8. System prompt rule added — LLM must use provided bias values exactly.
9. Removed BBCWorld and ECBNews — too broad / 403 blocked.
10. `classify_driver` upgraded to multi-label — returns `list[tuple[str, int]]`, threshold=2.
11. `aggregate_driver_signals` updated to loop ALL drivers per article.
12. `evidence.py` uses `classify_driver(article)[0]` for top driver in evidence card.
13. NewsAPI fetcher added — covers geopolitics, risk, central banks gaps.
14. FastAPI layer added (`app/main.py`) — `answer_question` now exposed as `POST /ask`.
15. `aggregate_driver_signals` now weights by keyword score (`+ score` instead of `+ 1`) — dominant drivers contribute more signal than secondary drivers.
16. `summarize_driver_impact` now appends signals proportionally using `range(count)` — fixes always-MIXED bias bug. rates(18) now correctly beats inflation(4).
17. Streamlit UI added (`app/streamlit_app.py`) — question input, time window selector, colored bias cards (🟢🔴🟡), analysis display.

---

## Known architectural limitations

1. `SCORE_THRESHOLD=2` hardcoded in `classify.py` — may need tuning as corpus grows.
2. NewsAPI free tier — limited daily calls, pageSize=10 per query.
3. Evidence card shows only top driver — multi-label not yet reflected in evidence display.
4. No scheduled ingestion — `refresh_news.py` must be run manually.
5. Streamlit embeddings recomputed on every question — no caching yet. Fix planned: `st.cache_resource`.
6. LLM answer repeats Market Bias section — already shown in UI cards. Fix planned: update system prompt.

---

## FastAPI layer (`app/main.py`)

Routes:
- `GET /health` — liveness check, returns `{"status": "ok"}`
- `POST /ask` — accepts `{"question": str, "days": int = 30}`, returns `{"question", "answer", "gold_bias", "silver_bias"}`

Request/response models use Pydantic (`AskRequest`, `AskResponse`). The handler calls `answer_question()` directly and unpacks the result dict into `AskResponse`.

> **Note:** `days` is accepted in the request but not yet forwarded into `answer_question` — recency is hardcoded to 30 days inside the function when called from FastAPI.

---

## Streamlit UI (`app/streamlit_app.py`)

- Question input with placeholder suggestions
- Time window selector (7 / 14 / 30 / 90 days)
- Colored bias cards — 🟢 supportive, 🔴 negative, 🟡 mixed, ⬜ unclear
- Full analysis display with markdown rendering
- Loading spinner during pipeline execution
- `sys.path` fix at top to resolve `src/` imports from `app/` folder

---

## Roadmap

| Priority | Feature |
|---|---|
| Done | Multi-source ingestion — RSS + FXStreet + NewsAPI |
| Done | Multi-label driver classification |
| Done | Market bias computation — weighted by score |
| Done | FastAPI endpoint — POST /ask + GET /health |
| Done | Streamlit UI — bias cards + analysis display |
| Next | Latency fix — `st.cache_resource` for embeddings |
| Next | Remove duplicate bias from LLM answer — update system prompt |
| After | Docker + Render deployment → live URL |
| After | Scheduled ingestion — APScheduler every 6 hours |
| After | Data retention — cleanup articles older than 6 months |
| After | Full article fetch — replace description with full text |
| After | Confidence scoring on bias |

---

## How to run

```bash
# Ingest fresh articles
python -m app.refresh_news

# Start the FastAPI server
uvicorn app.main:app --reload

# Start the Streamlit UI
streamlit run app/streamlit_app.py

# Ask a question directly (Python)
from src.llm.answer import answer_question
answer_question("What is driving gold prices right now?")
```

Manual tests live in `app/manual_tests/`.

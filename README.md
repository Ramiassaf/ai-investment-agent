# AI Investment Agent

## What Is This?

Gold and silver prices are driven by dozens of factors — Fed policy, geopolitical tensions, inflation data, USD movements, central bank activity. Tracking all of these manually across dozens of news sources is time-consuming and error-prone.

The AI Investment Agent automates that process. Ask a natural-language question, and the system:

1. Retrieves the most relevant recent financial articles using semantic search
2. Classifies each article across multiple market drivers (rates, inflation, geopolitics, USD, etc.)
3. Computes a directional market bias for gold and silver **programmatically** — before any LLM involvement
4. Returns a structured, evidence-backed research answer with citations

**This is not a financial advisor. It is a market research intelligence tool.**

---

## Live Demo

| Service | URL |
|---|---|
| 🖥️ Streamlit UI | https://ai-investment-agent-1.onrender.com |
| ⚡ FastAPI (Swagger) | https://ai-investment-agent-mw67.onrender.com/docs |
| 🔍 Health Check | https://ai-investment-agent-mw67.onrender.com/health |



---

## Example Output

**Question:** *"How are interest rate hikes affecting gold?"*

```json
{
  "question": "How are interest rate hikes affecting gold?",
  "answer": "1. Main Explanation\nInterest rate hikes are negatively impacting gold prices...",
  "gold_bias": "negative",
  "silver_bias": "negative"
}
```

**UI Output:**
```
Market Bias
Gold:   🔴 NEGATIVE
Silver: 🔴 NEGATIVE

Analysis:
Interest rate hikes are negatively impacting gold due to rising U.S. Treasury
yields and a stronger dollar. As interest rates increase, the opportunity cost
of holding non-yielding assets like gold rises...
```

---

## System Architecture

```
INGESTION LAYER
┌─────────────────────────────────────────────────────┐
│  RSS Feeds          FXStreet Scraper    NewsAPI      │
│  (FedMonetary,      (Gold + Silver      (6 targeted  │
│   Investing.com,     direct HTML)        queries)    │
│   GoldBroker)                                        │
└─────────────────────┬───────────────────────────────┘
                      │ ArticleRecord (standardized)
                      ▼
STORAGE LAYER
┌─────────────────────────────────────────────────────┐
│  article_store.py                                   │
│  → ArticleRecord dataclass                          │
│  → articles.jsonl (append-only, SHA-256 dedup)      │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
RETRIEVAL LAYER
┌─────────────────────────────────────────────────────┐
│  1. Domain Filter (keyword gate — 7 signal groups)  │
│  2. OpenAI Embeddings (text-embedding-3-small)       │
│  3. Cosine Similarity Search (top-5 articles)        │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
DOMAIN LAYER
┌─────────────────────────────────────────────────────┐
│  Multi-label Driver Classification (threshold=2)    │
│  Weighted Signal Aggregation (+score, not +1)        │
│  Programmatic Bias Computation (gold + silver)       │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
LLM LAYER
┌─────────────────────────────────────────────────────┐
│  Strict System Prompt (bias passed as constraint)   │
│  Evidence Cards (title, source, URL, snippet)        │
│  GPT-4o-mini → Structured Research Answer           │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
API / UI LAYER
┌─────────────────────────────────────────────────────┐
│  FastAPI  →  POST /ask  +  GET /health               │
│  Streamlit  →  Bias Cards + Analysis Display         │
└─────────────────────────────────────────────────────┘
```

---

## Key Engineering Decisions

| Decision | Why |
|---|---|
| **Multi-label classification** | Mixed-signal articles contribute to ALL relevant drivers — single-label silently lost geopolitics signals to macro keywords |
| **Weighted signal aggregation** | `+score` instead of `+1` — dominant drivers (score=18) outweigh secondary ones (score=4), fixing always-MIXED bias bug |
| **Programmatic bias before LLM** | Eliminates hallucination — LLM explains the bias, never derives it |
| **Domain filter before embeddings** | Cheap keyword gate removes irrelevant articles before expensive OpenAI API calls |
| **Two separate Dockerfiles** | Independent failure isolation, deployment cycles, and scaling for API vs UI |
| **Storage isolated in article_store.py** | JSONL → PostgreSQL migration only touches one file |
| **`st.cache_resource` for embeddings** | Embeds once at container start → 30s response time becomes 7s |

---

## Project Structure

```
ai-investment-agent/
│
├── app/                          # Entry points (runnable services)
│   ├── main.py                   # FastAPI app — POST /ask, GET /health
│   ├── streamlit_app.py          # Streamlit UI — question input, bias cards
│   ├── refresh_news.py           # Ingestion entry point — runs all sources
│   └── manual_tests/             # Manual test scripts
│       ├── test_answer.py
│       ├── test_driver_aggregate.py
│       ├── test_driver_summary.py
│       ├── test_format_driver_summary.py
│       ├── test_prompt_withreasoning.py
│       └── test_retrieval.py
│
├── src/                          # Core modules (reusable building blocks)
│   ├── storage/
│   │   └── article_store.py      # ArticleRecord dataclass, JSONL I/O, dedup
│   │
│   ├── ingestion/
│   │   ├── rss_fetcher.py        # Generic RSS fetcher with HTML guard
│   │   ├── rss_to_record.py      # RSS entry → ArticleRecord converter
│   │   ├── fxstreet_metals_fetcher.py  # Direct HTML scraper for FXStreet
│   │   └── newsapi_fetcher.py    # NewsAPI client — 6 targeted queries
│   │
│   ├── retrieval/
│   │   ├── domain_filter.py      # Keyword relevance gate — 7 signal groups
│   │   └── semantic_retriever.py # OpenAI embeddings + cosine similarity
│   │
│   ├── domain/
│   │   ├── classify.py           # Multi-label driver classifier
│   │   ├── drivers.py            # Driver → keyword lists
│   │   ├── driver_reasoning.py   # Signal aggregation, bias computation
│   │   └── evidence.py           # Evidence card builder
│   │
│   └── llm/
│       ├── client.py             # OpenAI API wrapper
│       ├── prompts.py            # System prompt + build_prompt()
│       └── answer.py             # Pipeline orchestrator (end-to-end)
│
├── data/
│   └── processed/
│       └── articles.jsonl        # Append-only article store
│
├── Dockerfile.api                # FastAPI container
├── Dockerfile.ui                 # Streamlit container
├── requirements.txt
├── CLAUDE.md                     # Project reference for Claude Code
└── .env                          # API keys (never committed)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI GPT-4o-mini |
| API Framework | FastAPI + Uvicorn |
| UI | Streamlit |
| Data Validation | Pydantic |
| Storage | JSONL (append-only flat file) |
| News Ingestion | feedparser, requests, BeautifulSoup, NewsAPI |
| Containerization | Docker (2 separate images) |
| Deployment | Render.com |

---

## Market Drivers Covered

| Driver | Keywords Include | Gold Impact | Silver Impact |
|---|---|---|---|
| `RATES_REAL_YIELDS` | Fed, interest rates, treasury yields | 🔴 Negative | 🔴 Negative |
| `USD_DOLLAR` | Dollar, DXY, greenback | 🔴 Negative | 🔴 Negative |
| `INFLATION` | CPI, PPI, consumer prices | 🟢 Supportive | 🟢 Supportive |
| `RISK_SENTIMENT` | Safe haven, recession fears, uncertainty | 🟢 Supportive | 🟡 Mixed |
| `GEOPOLITICS` | War, sanctions, Middle East, conflict | 🟢 Supportive | 🟡 Mixed |
| `CENTRAL_BANKS` | Gold reserves, central bank purchases | 🟢 Supportive | 🟡 Mixed |
| `SUPPLY_DEMAND_METALS` | Mining, industrial demand, silver demand | 🟡 Mixed | 🟢 Supportive |

---

## Run Locally

### Prerequisites
- Python 3.11+
- Docker Desktop
- OpenAI API key
- NewsAPI key (free tier: [newsapi.org](https://newsapi.org))

### 1. Clone and install

```bash
git clone https://github.com/Ramiassaf/ai-investment-agent.git
cd ai-investment-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Create .env file
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
NEWSAPI_KEY=your_key_here
```

### 3. Ingest articles

```bash
python -m app.refresh_news
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
# Visit: http://localhost:8000/docs
```

### 5. Run the UI

```bash
streamlit run app/streamlit_app.py
# Visit: http://localhost:8501
```

---

## Run with Docker

```bash
# Build images
docker build -f Dockerfile.api -t gold-api .
docker build -f Dockerfile.ui -t gold-ui .

# Run API
docker run -p 8000:8000 --env-file .env gold-api

# Run UI
docker run -p 8501:8501 --env-file .env gold-ui
```

---

## API Reference

### `POST /ask`

```json
// Request
{
  "question": "What is driving gold prices today?",
  "days": 30
}

// Response
{
  "question": "What is driving gold prices today?",
  "answer": "1. Main Explanation\n...",
  "gold_bias": "supportive",
  "silver_bias": "mixed"
}
```

### `GET /health`

```json
{ "status": "ok" }
```

---

## Roadmap

| Feature | Status |
|---|---|
| Multi-source ingestion — RSS + FXStreet + NewsAPI | ✅ Done |
| Multi-label driver classification | ✅ Done |
| Weighted market bias computation | ✅ Done |
| FastAPI REST endpoint | ✅ Done |
| Streamlit UI with cached embeddings | ✅ Done |
| Docker + Render deployment | ✅ Done |

---

## Author

**Rami Assaf**

---

*This project is for market research purposes only. It is not financial advice.*

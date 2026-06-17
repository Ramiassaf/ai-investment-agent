from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
import json
from dataclasses import asdict
from pathlib import Path
import hashlib
from email.utils import parsedate_to_datetime





@dataclass
class ArticleRecord:
    article_id: str
    source: str
    title: str
    url : str
    published_date : Optional[str]
    retrieved_at : str
    raw_text : str # before cleaning 
    clean_text: str # Making the text ready for llm 
    tags: list[str] # gold/silver/usd/inflation...
    
    def to_dict(self) -> dict:
        return asdict(self)


# Helper function to get current UTC time in ISO format
def get_current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



# Stable ID for deduplication
def make_article_id(url: str | None, source: str, title: str , published_date: str | None) -> str:
    """
    Stable ID for deduplication
    Priority: url; else (source + title + published_date)
    Solves RSS feeds Repetition.
    """
    base = (url or "").strip()
    if not base:
        base = f"{source.strip()}|{title.strip()}|{(published_date or'').strip()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


# Save a list of ArticleRecord to a JSONL file
def save_articles_jsonl(records: list[ArticleRecord],file_path: Path) -> None:
    file_path.parent.mkdir(parents=True,exist_ok=True)
    with file_path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")


# Append only unseen articles to JSONL
def save_articles_jsonl_dedup(path: str | Path, new_articles: list[ArticleRecord]) -> dict:
    """
    Append only unseen articles to JSONL
    Return stats
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_articles_jsonl(path)
    seen_ids = {a.article_id for a in existing}

    to_write = [a for a in new_articles if a.article_id not in seen_ids]
    save_articles_jsonl(to_write, path)
    return {
        "existing": len(existing),
        "incoming": len(new_articles),
        "written": len(to_write),
        "skipped_duplicates": len(new_articles) - len(to_write),
        "final_total_estimate": len(existing) + len(to_write),
    }



# Load articles from a JSONL file, returning a list of ArticleRecord
def load_articles_jsonl(path: str | Path)-> list[ArticleRecord]:
    path = Path(path)
    if not path.exists():
        return []
    
    records : list[ArticleRecord] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(ArticleRecord(**obj))
            except Exception as e:
                print(f"[article_store] skipping bad line {line_no}: {e}")
                continue
    return records


# Parse published_date from either ISO-8601 or RSS/HTTP date
def _parse_published_date(s: str) -> datetime | None:
    """
    Parse published_date from either:
    - ISO-8601 (e.g., 2026-02-24T09:00:00+00:00)
    - RSS/HTTP date (e.g., Tue, 24 Feb 2026 09:00:00 GMT)
    Returns timezone-aware UTC datetime, or None if unparseable.
    """
    if not s:
        return None

    s = s.strip()

    # Try ISO first
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try RSS/HTTP date (RFC 2822)
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
    

# Filter articles by recency (e.g., last 7 days)
def filter_by_recency(articles: list[ArticleRecord], days: int = 7) -> list[ArticleRecord]:
    """
    Return only articles published within the last `n-days`.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    fresh = []

    for a in articles:
        if not a.published_date:
            continue

        try:
            dt = _parse_published_date(a.published_date.replace("Z", "+00:00"))
        except Exception:
            continue

        if dt >= cutoff:
            fresh.append(a)

    return fresh





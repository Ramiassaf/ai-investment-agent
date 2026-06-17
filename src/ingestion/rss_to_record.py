from typing import Optional
from src.storage.article_store import ArticleRecord,  get_current_utc_iso, make_article_id

def pick_date(entry: dict) -> Optional [str]:
    # feedparser often use 'published' or 'updated' for date
    return entry.get("published") or entry.get("updated")

def clean_text_from_entry(entry:dict)-> str:
    # Many RSS Feeds provide summary/description
    # we'll use summary as "clean_text" for now day 10 we fetch full article html 
    return (entry.get("summary") or entry.get("description") or "").strip()

def tags_from_entry(entry: dict)-> list[str]:
    #feedparser may provide tags as list of dicts:[{'term':'Gold'},...]
    raw = entry.get("tags")or[]
    out = []
    for t in raw:
        term = (t.get("term") or "").strip()
        if term:
            out.append(term.lower())
    return out

def entry_to_article_record(entry: dict, source_name: str) -> ArticleRecord:
   title = (entry.get("title") or "").strip()
   url = (entry.get("link") or "").strip()
   published_date = pick_date(entry)
   retrieved_at = get_current_utc_iso()

   clean_text = clean_text_from_entry(entry)
   raw_text = clean_text

   # Stable ID
   article_id = make_article_id(url or None, source_name, title, published_date)

   return ArticleRecord(
       article_id=article_id,
       source=source_name,
       title=title,
       url=url,
       published_date=published_date,
       retrieved_at=retrieved_at,
       raw_text=raw_text,
       clean_text=clean_text,
       tags=tags_from_entry(entry),
   )
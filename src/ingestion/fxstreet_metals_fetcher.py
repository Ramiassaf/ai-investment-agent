from datetime import datetime, timezone
import hashlib
import requests
from bs4 import BeautifulSoup

from src.storage.article_store import ArticleRecord

GOLD_PAGE_URL = "https://www.fxstreet.com/markets/commodities/metals/gold"
SILVER_PAGE_URL = "https://www.fxstreet.com/news?q=silver"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def make_article_id(url: str)->str:
    """
    Create stable article id from URL
    """
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:24]



def extract_fxstreet_links(page_url: str, keywords: list[str]) -> list[tuple[str, str]]:
    """
    Extract real FXstreet gold article links from the gold and silver page
    """
    response = requests.get(page_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]

        if not title:
            continue

        if href.startswith("/"):
            href = "https://www.fxstreet.com" + href

        if "/news/" not in href:
            continue

        title_lower = title.lower()
        if not any(keyword in title_lower for keyword in keywords):
            continue

        links.append((title, href))

    seen = set()
    unique_links = []

    for title, href in links:
        if href in seen:
            continue
        seen.add(href)
        unique_links.append((title, href))

    return unique_links



def fetch_fxstreet_article(url: str) -> ArticleRecord | None:
    """
    Fetch one FXstreet article and convert it into ArticleRecord
    """
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    paragraphs = soup.find_all("p")
    raw_text = "\n".join(
        p.get_text(strip=True)
        for p in paragraphs
        if p.get_text(strip=True)
    )

    if not title or not raw_text:
        return None

    article_id = make_article_id(url)
    retrieved_at = datetime.now(timezone.utc).isoformat()

    return ArticleRecord(
        article_id=article_id,
        source="fxstreet",
        title=title,
        url=url,
        published_date=None,
        retrieved_at=retrieved_at,
        raw_text=raw_text,
        clean_text=raw_text,
        tags=["gold", "fxstreet", "direct_source"],
    )




def fetch_fxstreet_metals_articles() -> list[ArticleRecord]:
    """
    Full FXStreet gold and silver ingestion:
    extract links → fetch articles → return ArticleRecords.
    """
    records = []

    sources = [
        {
            "name": "FXStreetGold",
            "page_url": GOLD_PAGE_URL,
            "keywords": ["gold", "xau"],
            "tags": ["gold", "fxstreet", "direct_source"],
        },
        {
            "name": "FXStreetSilver",
            "page_url": SILVER_PAGE_URL,
            "keywords": ["silver", "xag"],
            "tags": ["silver", "fxstreet", "direct_source"],
        },
    ]

    for source in sources:
        article_links = extract_fxstreet_links(
            page_url=source["page_url"],
            keywords=source["keywords"],
        )

        print(f"{source['name']}: found {len(article_links)} links")

        for title, url in article_links:
            try:
                record = fetch_fxstreet_article(url)

                if record:
                    record.source = source["name"]
                    record.tags = source["tags"]
                    records.append(record)

            except Exception as e:
                print(f"[{source['name']}] Skipped article: {url} | Error: {e}")

    return records

if __name__ == "__main__":
    records = fetch_fxstreet_metals_articles()

    print(f"Fetched {len(records)} FXStreet metals articles")

    for r in records[:5]:
        print(r.source, r.title)
        print(r.url)
        print(r.tags)
        print("------")
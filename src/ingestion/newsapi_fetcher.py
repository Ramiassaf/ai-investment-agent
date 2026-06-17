import requests
from src.storage.article_store import ArticleRecord, make_article_id, get_current_utc_iso

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

QUERIES = [
    '("Federal Reserve" OR Fed OR ECB OR "interest rates") AND (gold OR silver)',
    '("geopolitical tensions" OR war OR sanctions OR conflict) AND (gold OR silver)',
    '("solar demand" OR EV OR "industrial demand") AND silver',
    '("US dollar" OR DXY OR "Treasury yields") AND (gold OR silver)',
    '("central bank purchases" OR "gold reserves") AND gold',
    '(recession OR stagflation OR "economic uncertainty") AND (gold OR silver)',
]

QUERY_TAGS = [
    ["newsapi", "gold", "silver", "rates", "inflation", "central_banks"],
    ["newsapi", "gold", "silver", "geopolitics", "risk"],
    ["newsapi", "silver", "industrial", "supply_demand"],
    ["newsapi", "gold", "silver", "usd", "rates"],
    ["newsapi", "gold", "central_banks", "supply_demand"],
    ["newsapi", "gold", "silver", "risk", "inflation"],
]


def fetch_newsapi_articles(api_key: str, page_size: int = 10) -> list[ArticleRecord]:
    records = []
    seen_ids = set()

    for query, tags in zip(QUERIES, QUERY_TAGS):
        try:
            response = requests.get(NEWSAPI_BASE_URL, params={
                "q": query,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
            }, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[newsapi_fetcher] request failed for query '{query[:60]}...': {e}")
            continue

        data = response.json()

        if data.get("status") != "ok":
            print(f"[newsapi_fetcher] API error: {data.get('message', 'unknown')}")
            continue

        for article in data.get("articles", []):
            url = (article.get("url") or "").strip()
            title = (article.get("title") or "").strip()

            if not url or not title or title == "[Removed]":
                continue

            article_id = make_article_id(url, "NewsAPI", title, article.get("publishedAt"))

            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)

            description = (article.get("description") or "").strip()

            records.append(ArticleRecord(
                article_id=article_id,
                source="NewsAPI",
                title=title,
                url=url,
                published_date=article.get("publishedAt"),
                retrieved_at=get_current_utc_iso(),
                raw_text=description,
                clean_text=description,
                tags=tags,
            ))

    print(f"[newsapi_fetcher] fetched {len(records)} unique articles across {len(QUERIES)} queries")
    return records
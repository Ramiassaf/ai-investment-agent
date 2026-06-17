from pathlib import Path
import os
from dotenv import load_dotenv
from src.ingestion.rss_fetcher import fetch_rss_feed
from src.ingestion.rss_to_record import entry_to_article_record
from src.storage.article_store import save_articles_jsonl_dedup
from src.ingestion.fxstreet_metals_fetcher import fetch_fxstreet_metals_articles
from src.ingestion.newsapi_fetcher import fetch_newsapi_articles


load_dotenv()
api_key = os.getenv("NEWSAPI_KEY")



DATA_PATH = Path("data/processed/articles.jsonl")

FEEDS = [
    ("FedMonetary", "https://www.federalreserve.gov/feeds/press_monetary.xml"),
    ("InvestingCommoditiesNews", "https://www.investing.com/rss/news_11.rss"),
    ("GoldBroker","https://www.goldbroker.com/en/news.rss"),
   
]

def main():
    all_new_records = []

    for source_name, url in FEEDS:
        try:
            entries = fetch_rss_feed(url, debug=True)
            print(f"{source_name}: fetched {len(entries)} entries")

            for e in entries:
                r = entry_to_article_record(e, source_name=source_name)
                if not r.title or not r.url:
                    continue
                all_new_records.append(r)

            print(f"Sample titles from {source_name}:")
            for e in entries[:3]:
                print(" -", e.get("title"))

        except Exception as e:
            print(f"[{source_name}] Skipped (fetch/parse failed): {e}")
            continue
    # FXStreet direct source runs once, after RSS feeds   
    try:
        fxstreet_records = fetch_fxstreet_metals_articles()
        print(f"FXStreetGold: fetched {len(fxstreet_records)} articles")
        all_new_records.extend(fxstreet_records)
    except Exception as e:
        print(f"[FXStreetGold] Skipped: {e}")


    print("Total new records prepared:", len(all_new_records))   

    if api_key:
        try:
            newsapi_records = fetch_newsapi_articles(api_key, page_size=10)
            print(f"NewsAPI: fetched {len(newsapi_records)} articles")
            all_new_records.extend(newsapi_records)
        except Exception as e:
            print(f"[NewsAPI] Skipped: {e}")
    else:
        print("[NewsAPI] Skipped: NEWSAPI_KEY not set in .env")     

    stats = save_articles_jsonl_dedup(DATA_PATH, all_new_records)
    print("Save stats:", stats)

if __name__ == "__main__":
    main()
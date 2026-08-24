from src.storage.article_store import cleanup_old_articles

stats = cleanup_old_articles("data/processed/articles.jsonl", keep_days=180)
print(stats)
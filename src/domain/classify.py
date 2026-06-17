from src.domain.drivers import GOLD_SILVER_DRIVERS
from src.storage.article_store import ArticleRecord

SCORE_THRESHOLD = 2

def classify_driver(article: ArticleRecord) -> list[tuple[str, int]]:
    """
    Returns all drivers whose keyword match count >= SCORE_THRESHOLD,
    sorted by score descending. Returns [("OTHER", 0)] if none qualify.
    """
    text = f"{article.title} {article.clean_text} {' '.join(article.tags or [])}".lower()
    scores = {}
    for driver, keywords in GOLD_SILVER_DRIVERS.items():
        hit_count = sum(1 for kw in keywords if kw in text)
        if hit_count:
            scores[driver] = hit_count

    qualified = [(driver, score) for driver, score in scores.items() if score >= SCORE_THRESHOLD]

    if not qualified:
        return [("OTHER", 0)]

    return sorted(qualified, key=lambda x: x[1], reverse=True)
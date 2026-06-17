from src.storage.article_store import ArticleRecord
from src.domain.classify import classify_driver

def make_evidence_card(article: ArticleRecord) -> dict:
    driver, score = classify_driver(article)[0]

    return{
        "title": article.title,
        "source": article.source,
        "published_date": article.published_date,
        "url": article.url,
        "driver": driver,
        "driver_score": score,
        "snippet": (article.clean_text[:220] + "...") if article.clean_text and len(article.clean_text) > 220 else article.clean_text
    }

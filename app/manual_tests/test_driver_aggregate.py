from src.domain.driver_reasoning import aggregate_driver_signals, analyze_article_drivers
from src.storage.article_store import ArticleRecord


def main():
    articles = [
        ArticleRecord(
            article_id="1",
            source="test",
            title="",
            url="",
            published_date="",
            retrieved_at="",
            raw_text="",
            clean_text="Inflation is rising",
            tags=[]
      ),
        ArticleRecord(
            article_id="2",
            source="test",
            title="",
            url="",
            published_date="",
            retrieved_at="",
            raw_text="",
            clean_text="Interest rates are increasing",
            tags=[]
        ),
        ArticleRecord(
            article_id="3",
            source="test",
            title="",
            url="",
            published_date="",
            retrieved_at="",
            raw_text="",
            clean_text="Rates continue to rise",
            tags=[]
        )
    ]

    result = aggregate_driver_signals(articles)
    print(result)


if __name__ == "__main__":
    main()
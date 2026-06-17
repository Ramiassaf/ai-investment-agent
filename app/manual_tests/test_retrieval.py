from src.storage.article_store import load_articles_jsonl, filter_by_recency   
from src.retrieval.semantic_retriever import (
    prepare_retrieval_corpus,  embed_texts, semantic_search)
from src.retrieval.domain_filter import filter_domain_relevant_articles


articles = load_articles_jsonl("data/processed/articles.jsonl")
recent_articles = filter_by_recency(articles, days=30)
domain_articles, domain_debug = filter_domain_relevant_articles(recent_articles)
corpus = prepare_retrieval_corpus(domain_articles )
embeddings = embed_texts(corpus)

test_queries =[
    "Why is gold going higher?",
    "How do central banks affect gold?",
    "How do geopolitical tensions affect gold?",
    "Why would interest rates matter for silver?"
]


for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"\n{'='*60}")
    
    results = semantic_search(
        query = query,
        articles = domain_articles,
        embeddings = embeddings,
        top_k = 5
    )
    print(f"Total recent articles: {len(recent_articles)}")
    print(f"Domain relevant articles: {len(domain_articles)}")

    for r in domain_debug[:5]:
        print(r["title"],"->", r["reason"],  r["matched_groups"])

    for i,r in enumerate(results, start=1):
        print(f"{i}. {r.title}")


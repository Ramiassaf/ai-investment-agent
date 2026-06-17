from src.storage.article_store import load_articles_jsonl, filter_by_recency
from src.domain.evidence import make_evidence_card
from src.domain.driver_reasoning import (aggregate_driver_signals, summarize_driver_impact, 
format_driver_summary, compute_market_bias)
from src.retrieval.domain_filter import filter_domain_relevant_articles
from src.retrieval.semantic_retriever import (
    prepare_retrieval_corpus,
    embed_texts,
    semantic_search,
)
from src.llm.client import generate_answer
from src.llm.prompts import build_prompt


def answer_question(question: str, domain_articles=None, embeddings=None):

    # if not provided, compute fresh (FastAPI path)
    if domain_articles is None or embeddings is None:
        articles = load_articles_jsonl("data/processed/articles.jsonl")
        if not articles:
            return {
                "question": question,
                "answer": "No articles found. Run refresh_news.py first.",
                "gold_bias": "unclear",
                "silver_bias": "unclear"
            }
        recent_articles = filter_by_recency(articles, days=30)
        if not recent_articles:
            return {
                "question": question,
                "answer": "No recent articles found (last 30 days).",
                "gold_bias": "unclear",
                "silver_bias": "unclear"
            }
        domain_articles, _ = filter_domain_relevant_articles(recent_articles)
        if not domain_articles:
            return {
                "question": question,
                "answer": "No domain-relevant articles found.",
                "gold_bias": "unclear",
                "silver_bias": "unclear"
            }
        corpus = prepare_retrieval_corpus(domain_articles)
        embeddings = embed_texts(corpus)

    # from here — same for both paths (Streamlit cached or FastAPI fresh)
    hits = semantic_search(question, domain_articles, embeddings, top_k=5)
    if not hits:
        return {
            "question": question,
            "answer": "Semantic search returned no results.",
            "gold_bias": "unclear",
            "silver_bias": "unclear"
        }

    evidence = [make_evidence_card(a) for a in hits]

    driver_counts = aggregate_driver_signals(hits)
    driver_summary = summarize_driver_impact(driver_counts)
    gold_bias = compute_market_bias(driver_summary["gold"])
    silver_bias = compute_market_bias(driver_summary["silver"])
    driver_reasoning = format_driver_summary(driver_summary)
    system_prompt, user_prompt = build_prompt(question, evidence, driver_reasoning, gold_bias, silver_bias)

    response = generate_answer(system_prompt, user_prompt)

    print("\nANSWER:")
    print(response)
    return {
        "question": question,
        "answer": response,
        "gold_bias": gold_bias,
        "silver_bias": silver_bias
    }
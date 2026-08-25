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
from src.storage.article_store import get_current_utc_iso
import time

SIMILARITY_THRESHOLD = 0.3


def _log_and_return(question, answer, gold_bias, silver_bias, start_time):
    elapsed = time.time() - start_time
    print(f"[USAGE] {get_current_utc_iso()} | question={question} | gold={gold_bias} | silver={silver_bias} | elapsed={elapsed:.2f}s")
    return {
        "question": question,
        "answer": answer,
        "gold_bias": gold_bias,
        "silver_bias": silver_bias
    }


def answer_question(question: str, domain_articles=None, embeddings=None):
    start = time.time()

    if domain_articles is None or embeddings is None:
        articles = load_articles_jsonl("data/processed/articles.jsonl")
        if not articles:
            return _log_and_return(question, "No articles found. Run refresh_news.py first.", "unclear", "unclear", start)

        recent_articles = filter_by_recency(articles, days=30)
        if not recent_articles:
            return _log_and_return(question, "No recent articles found (last 30 days).", "unclear", "unclear", start)

        domain_articles, _ = filter_domain_relevant_articles(recent_articles)
        if not domain_articles:
            return _log_and_return(question, "No domain-relevant articles found.", "unclear", "unclear", start)

        corpus = prepare_retrieval_corpus(domain_articles)
        embeddings = embed_texts(corpus)

    hits, top_score = semantic_search(question, domain_articles, embeddings, top_k=5)
    if not hits:
        return _log_and_return(question, "Semantic search returned no results.", "unclear", "unclear", start)

    if top_score < SIMILARITY_THRESHOLD:
        return _log_and_return(
            question,
            "This question doesn't appear to be about gold or silver markets. "
            "Try asking about price drivers, Fed policy, inflation, or geopolitical impacts on precious metals.",
            "unclear",
            "unclear",
            start
        )

    evidence = [make_evidence_card(a) for a in hits]

    driver_counts = aggregate_driver_signals(hits)
    driver_summary = summarize_driver_impact(driver_counts)
    gold_bias = compute_market_bias(driver_summary["gold"])
    silver_bias = compute_market_bias(driver_summary["silver"])
    driver_reasoning = format_driver_summary(driver_summary)
    system_prompt, user_prompt = build_prompt(question, evidence, driver_reasoning, gold_bias, silver_bias)

    response = generate_answer(system_prompt, user_prompt)

    return _log_and_return(question, response, gold_bias, silver_bias, start)
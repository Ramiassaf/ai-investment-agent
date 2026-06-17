from __future__ import annotations

from typing import Any

from src.storage.article_store import ArticleRecord


DIRECT_METALS_TERMS = {
    "gold",
    "silver",
    "precious metal",
    "precious metals",
    "bullion",
    "spot gold",
    "spot silver",
    "gold price",
    "silver price",
}

RATES_YIELDS_TERMS = {
    "fed",
    "federal reserve",
    "interest rate",
    "interest rates",
    "rate cut",
    "rate cuts",
    "rate hike",
    "rate hikes",
    "yield",
    "yields",
    "real yield",
    "real yields",
    "treasury yield",
    "treasury yields",
    "bond yield",
    "bond yields",
}

INFLATION_TERMS = {
    "inflation",
    "cpi",
    "ppi",
    "consumer prices",
    "producer prices",
    "price pressures",
    "sticky inflation",
    "disinflation",
}

USD_TERMS = {
    "dollar",
    "us dollar",
    "usd",
    "dxy",
    "greenback",
    "dollar index",
}

RISK_GEOPOLITICS_TERMS = {
    "safe haven",
    "risk-off",
    "uncertainty",
    "recession fears",
    "war",
    "conflict",
    "sanctions",
    "middle east",
    "ukraine",
    "military escalation",
    "geopolitical tensions",
}

CENTRAL_BANKS_TERMS = {
    "central bank",
    "central banks",
    "reserves",
    "gold reserves",
    "gold buying",
    "reserve diversification",
    "monetary policy",
}

SUPPLY_DEMAND_TERMS = {
    "mining",
    "mine supply",
    "production",
    "output",
    "jewelry demand",
    "industrial demand",
    "silver demand",
    "metal demand",
    "refinery",
    "supply disruption",
}

SIGNAL_GROUPS = {
    "direct_metals": DIRECT_METALS_TERMS,
    "rates_yields": RATES_YIELDS_TERMS,
    "inflation": INFLATION_TERMS,
    "usd": USD_TERMS,
    "risk_geopolitics": RISK_GEOPOLITICS_TERMS,
    "central_banks": CENTRAL_BANKS_TERMS,
    "supply_demand": SUPPLY_DEMAND_TERMS,
}

def build_domain_filter(article: ArticleRecord) ->str:
    """
    Build one normalized text string used for domain matching.
    """
    parts = [
        article.title or "",
        article.clean_text or "",
        " ".join(article.tags) if article.tags else "",
    ]
    return " ".join(parts).lower().strip()


def evaluate_article_domain_filter(article: ArticleRecord) -> dict[str, Any]:
    """
    Evaluate whether one article is relevant enough for the gold/silver retrieval domain
    
    Pass rules:
    - pass immediately if direct metals group matches
    - otherwise, pass if at least 2 non-direct groups match
    """
    text  = build_domain_filter(article)

    matched_groups : list[str] = []
    matched_terms : list[str] = []

    for group_name, terms in SIGNAL_GROUPS.items():
        group_hits = [term for term in terms if term in text]
        if group_hits:
            matched_groups.append(group_name)
            matched_terms.extend(group_hits)
    
    matched_groups = sorted(set(matched_groups))
    matched_terms = sorted(set(matched_terms))

    direct_match = "direct_metals" in matched_groups
    non_direct_groups = list(g for g in matched_groups if g != "direct_metals")

    score= 0
    if direct_match:
        score+=3
        
    score+= len(list(non_direct_groups))

    if direct_match:
        is_relevant = True
        reason = " passed direct metals"
    
    elif len(non_direct_groups) >= 2:
        is_relevant = True
        reason = f" passed with {len(non_direct_groups)} multi macro groups"
    else:
        is_relevant = False
        reason = " did not pass failed insufficient multi macro groups and no direct metals"

    return {
        "article_id": article.article_id,
        "title": article.title,
        "is_relevant": is_relevant,
        "score": score,
        "matched_groups": matched_groups,
        "matched_terms": matched_terms,
        "reason": reason,
    }


def filter_domain_relevant_articles( articles: list[ArticleRecord]) -> tuple[list[ArticleRecord], list[dict[str, Any]]]:
    """
    Filte a list f articles down to domain_relevant ones.
    Returns:
    - filtered articles
    - debug results for all evaluated articles
    """
    filtered_articles : list[ArticleRecord] = []
    debug_results : list[dict[str, Any]] = []

    for article in articles:
        result = evaluate_article_domain_filter(article)
        debug_results.append(result)
        if result["is_relevant"]:
            filtered_articles.append(article)
    return filtered_articles, debug_results
   
DRIVER_IMPACT = {
    "inflation": {
        "gold": "supportive",
        "silver": "supportive",
        "explanation": "Inflation reduces purchasing power, increasing demand for precious metals."
    },
    "rates": {
        "gold": "negative",
        "silver": "negative",
        "explanation": "Higher interest rates increase bond yields, reducing attractiveness of non-yielding assets like gold."
    },
    "usd": {
        "gold": "negative",
        "silver": "negative",
        "explanation": "A stronger US dollar makes gold and silver more expensive for other currencies."
    },
    "risk": {
        "gold": "supportive",
        "silver": "mixed",
        "explanation": "In times of uncertainty, investors move toward safe-haven assets like gold."
    },
    "central_banks": {
    "gold": "supportive",
    "silver": "mixed",
    "explanation": "Central bank gold purchases and reserve accumulation increase demand for gold, while silver is less directly affected."
    },

    "supply_demand": {
    "gold": "mixed",
    "silver": "supportive",
    "explanation": "Changes in metal supply and industrial demand can impact prices, with silver more sensitive due to its industrial usage, while gold is less affected."
    }
}

DRIVER_NAME_MAP = {
    "RATES_REAL_YIELDS": "rates",
    "USD_DOLLAR": "usd",
    "INFLATION": "inflation",
    "RISK_SENTIMENT": "risk",
    "GEOPOLITICS": "risk",
    "CENTRAL_BANKS": "central_banks",
    "SUPPLY_DEMAND_METALS": "supply_demand",
}


from src.domain.classify import classify_driver


def get_driver_impact(driver: str)-> dict:
    return DRIVER_IMPACT.get(driver, {})




# Analyze single Article Impact
def analyze_article_drivers(article)  -> list[dict]:
    """
    Given an article, detect drivers and return their impact.
    """

    results = []
    for driver_name, score in classify_driver(article):
        base_driver = DRIVER_NAME_MAP.get(driver_name)
        if not base_driver:
            continue
        impact = get_driver_impact(base_driver)
        if not impact:
            continue
        results.append({
            "driver": driver_name,
            "gold": impact.get("gold"),
            "silver": impact.get("silver"),
            "explanation": impact.get("explanation"),
        })
    return results
    

# Multi-article aggregation driver signals
def aggregate_driver_signals(articles)-> dict:
    """
    Aggregate driver signals from a multiple of articles to understand what is dominating the market now.
    """

    driver_counts = {}

    for article in articles:
        for driver_name, score in classify_driver(article):
            base_driver = DRIVER_NAME_MAP.get(driver_name)
            if not base_driver:
                continue
            driver_counts[base_driver] = driver_counts.get(base_driver, 0) + score

    return driver_counts


# Summarize Driver Impact

def summarize_driver_impact(driver_counts: dict)-> dict:
    """
    convert aggregated drivers into final gold & silver view (structured impact)
    """
    summary = {
        "gold": [],
        "silver": [],
        "details": []
    }
    for driver, count in driver_counts.items():
        impact = get_driver_impact(driver)
        if not impact:
            continue

        gold_effect = impact.get("gold")
        silver_effect = impact.get("silver")
        
        for _ in range(count):
            summary["gold"].append(gold_effect)
            summary["silver"].append(silver_effect)
            
        summary["details"].append(
            f"{driver} ({count}) -> gold: {gold_effect}, silver: {silver_effect}"
        
        )
       

    return summary


# Convert summary to Prompt Ready Text
def format_driver_summary(summary:dict)-> str:
    """
    Convert driver summary dict into prompt ready text
    """

    lines = ["Driver Reasoning Summary:"]

    details = summary.get("details",[])
    if not details:
        return "Driver Reasoning Summary:\n NO clear driver signals detected."
    
    for item in details:
        lines.append(f"- {item}")

    gold_signals = ", ".join(summary.get("gold", [])) or "no clear signals"
    silver_signals = ", ".join(summary.get("silver", [])) or "no clear signals"

    lines.append("")
    lines.append(f"Gold signals: {gold_signals}")
    lines.append(f"Silver signals: {silver_signals}")
    return "\n".join(lines)


# Compute Market Bias from Driver Signal

def compute_market_bias(signals : list[str])-> str:
    """
    Compute final market bias from dirver signals.
    """

    if not signals:
        return "unclear"
    
    supportive_count = signals.count("supportive")
    negative_count = signals.count("negative")

    if supportive_count > negative_count:
        return "supportive"
    
    if negative_count > supportive_count:
        return "negative"
    
    return "mixed"
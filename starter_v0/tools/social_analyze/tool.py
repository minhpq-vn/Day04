from __future__ import annotations

import re
from collections import Counter
from typing import Any

from tools._shared import fold_text, terms


POSITIVE_TERMS = {
    "amazing", "awesome", "best", "better", "cool", "excellent", "excited", "fast", "good", "great",
    "happy", "impressive", "love", "nice", "recommend", "strong", "success", "win",
    "tot", "hay", "thich", "yeu", "manh", "an tuong", "xuat sac", "nen dung", "thanh cong",
}

NEGATIVE_TERMS = {
    "angry", "bad", "broken", "bug", "complaint", "crash", "delay", "disappointed", "fail", "hate",
    "issue", "lawsuit", "problem", "risk", "scam", "slow", "terrible", "worse", "worst",
    "te", "loi", "cham", "hong", "that vong", "phan nan", "khieu nai", "lua dao", "rui ro", "khung hoang",
}

RISK_TERMS = {
    "boycott", "complaint", "crisis", "fraud", "lawsuit", "leak", "recall", "scam", "security",
    "khung hoang", "kien", "ro ri", "thu hoi", "lua dao", "bao mat", "tay chay", "khieu nai",
}

THEME_HINTS: dict[str, set[str]] = {
    "Product quality": {"bug", "broken", "crash", "feature", "quality", "slow", "update", "loi", "hong", "cham"},
    "Customer support": {"support", "service", "refund", "warranty", "help", "bao hanh", "ho tro", "dich vu"},
    "Pricing": {"price", "pricing", "cost", "cheap", "expensive", "sale", "discount", "gia", "dat", "re"},
    "Launch/news": {"announce", "launch", "release", "new", "event", "ra mat", "cong bo", "tin"},
    "Competitor comparison": {"vs", "versus", "compare", "better", "worse", "doi thu", "so sanh"},
    "Brand reputation": {"brand", "trust", "love", "hate", "boycott", "reputation", "thuong hieu", "uy tin"},
}


def _text(item: dict[str, Any]) -> str:
    return f"{item.get('title') or ''} {item.get('summary') or ''}".strip()


def _metric_value(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower().replace(",", "")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([km]?)", text)
    if not match:
        return 0
    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    return int(number)


def _engagement(item: dict[str, Any]) -> int:
    metrics = item.get("metrics") or {}
    return (
        _metric_value(metrics.get("favorites"))
        + _metric_value(metrics.get("retweets")) * 2
        + _metric_value(metrics.get("views")) // 100
    )


def _sentiment(text: str) -> str:
    folded = fold_text(text)
    positive = sum(1 for term in POSITIVE_TERMS if term in folded)
    negative = sum(1 for term in NEGATIVE_TERMS if term in folded)
    if negative > positive:
        return "negative"
    if positive > negative:
        return "positive"
    return "neutral"


def _themes(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    counters: Counter[str] = Counter()
    all_terms: Counter[str] = Counter()
    query_terms = terms(query)

    for item in items:
        item_terms = terms(_text(item))
        all_terms.update(term for term in item_terms if term not in query_terms)
        folded = fold_text(_text(item))
        for theme, hints in THEME_HINTS.items():
            if any(hint in folded for hint in hints):
                counters[theme] += 1

    themes = [{"name": name, "mentions": count} for name, count in counters.most_common(5)]
    if themes:
        return themes
    return [{"name": term, "mentions": count} for term, count in all_terms.most_common(5)]


def _risk_level(items: list[dict[str, Any]], sentiment_counts: Counter[str]) -> str:
    if not items:
        return "unknown"
    negative_ratio = sentiment_counts["negative"] / len(items)
    risk_hits = sum(1 for item in items if any(term in fold_text(_text(item)) for term in RISK_TERMS))
    if negative_ratio >= 0.45 or risk_hits >= 3:
        return "high"
    if negative_ratio >= 0.25 or risk_hits >= 1:
        return "medium"
    return "low"


def _key_posts(items: list[dict[str, Any]], max_examples: int) -> list[dict[str, Any]]:
    ranked = sorted(items, key=_engagement, reverse=True)
    results = []
    for item in ranked[:max(1, int(max_examples or 3))]:
        results.append({
            "title": item.get("title") or "",
            "summary": item.get("summary") or "",
            "source": item.get("source") or "",
            "url": item.get("url") or "",
            "date": item.get("date"),
            "metrics": item.get("metrics") or {},
            "engagement_score": _engagement(item),
            "sentiment": _sentiment(_text(item)),
        })
    return results


def _brief(
    query: str,
    focus: str,
    sentiment_counts: Counter[str],
    themes: list[dict[str, Any]],
    risk_level: str,
    key_posts: list[dict[str, Any]],
    total: int,
) -> str:
    title = focus or query or "Social listening"
    parts = [
        f"# Social Listening Brief: {title}",
        "",
        f"- Posts analyzed: {total}",
        (
            "- Sentiment: "
            f"{sentiment_counts['positive']} positive, "
            f"{sentiment_counts['neutral']} neutral, "
            f"{sentiment_counts['negative']} negative"
        ),
        f"- Risk level: {risk_level}",
        "",
        "## Main Themes",
    ]
    if themes:
        parts.extend(f"- {theme['name']} ({theme['mentions']} mentions)" for theme in themes)
    else:
        parts.append("- Not enough signal to identify themes.")

    parts.extend(["", "## Key Posts"])
    if key_posts:
        for post in key_posts:
            source = post["source"] or "social"
            link = f" - {post['url']}" if post["url"] else ""
            text = (post["summary"] or post["title"]).replace("\n", " ")
            if len(text) > 180:
                text = text[:177] + "..."
            parts.append(f"- [{post['sentiment']}] {text} ({source}){link}")
    else:
        parts.append("- No posts available.")

    parts.extend(["", "## Recommended Action"])
    if risk_level == "high":
        parts.append("- Escalate to PR/support, inspect negative posts manually, and prepare a response plan.")
    elif risk_level == "medium":
        parts.append("- Keep monitoring and respond to concrete complaints or factual questions.")
    elif total:
        parts.append("- Continue lightweight monitoring; no urgent action is visible from this sample.")
    else:
        parts.append("- Broaden the query or collect more posts before drawing conclusions.")
    return "\n".join(parts)


def analyze_social_items(
    items: list[dict[str, Any]] | None = None,
    query: str = "",
    focus: str = "",
    max_examples: int = 3,
) -> dict[str, Any]:
    items = items or []
    sentiments = Counter(_sentiment(_text(item)) for item in items)
    themes = _themes(items, query or focus)
    risk = _risk_level(items, sentiments)
    posts = _key_posts(items, max_examples)
    return {
        "tool": "analyze_social_items",
        "query": query,
        "focus": focus,
        "total_items": len(items),
        "sentiment_counts": {
            "positive": sentiments["positive"],
            "neutral": sentiments["neutral"],
            "negative": sentiments["negative"],
        },
        "themes": themes,
        "risk_level": risk,
        "key_posts": posts,
        "brief_markdown": _brief(query, focus, sentiments, themes, risk, posts, len(items)),
    }

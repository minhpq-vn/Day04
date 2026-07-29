from __future__ import annotations

import re
from typing import Any

from tools._shared import err

POS_WORDS = {"tốt", "tuyệt", "thích", "ngon", "xịn", "đẹp", "khen", "yêu", "hài lòng", "uy tín", "chất lượng", "ấn tượng", "đỉnh", "good", "great", "love", "awesome", "excellent", "best", "like"}
NEG_WORDS = {"lỗi", "tệ", "kém", "chậm", "dở", "hỏng", "ghét", "phàn nàn", "khiếu nại", "thất vọng", "đắt", "bán tháo", "scandal", "phát nổ", "cháy", "bad", "worst", "fail", "slow", "error", "horrible", "terrible", "issue", "bug"}

def analyze_sentiment(items: list[dict[str, Any]] | None = None, query: str = "") -> dict[str, Any]:
    """Analyze sentiment breakdown, media risk score, and key recommendations from social items."""
    try:
        items = items or []
        if not items and not query:
            return {
                "tool": "analyze_sentiment",
                "query": query,
                "total_posts": 0,
                "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0},
                "overall_sentiment": "Neutral",
                "risk_score": "0%",
                "key_issues": ["Không có dữ liệu bài đăng để phân tích."],
                "recommended_actions": ["Thu thập thêm bài đăng từ social_search trước khi phân tích."]
            }

        pos_count = 0
        neg_count = 0
        neu_count = 0
        issues = set()

        for item in items:
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            words = set(re.findall(r'\w+', text))
            
            pos_matches = words.intersection(POS_WORDS)
            neg_matches = words.intersection(NEG_WORDS)
            
            if len(neg_matches) > len(pos_matches):
                neg_count += 1
                for w in neg_matches:
                    issues.add(f"Phản hồi về '{w}'")
            elif len(pos_matches) > len(neg_matches):
                pos_count += 1
            else:
                neu_count += 1

        total = len(items) if items else 1
        pos_ratio = pos_count / total
        neg_ratio = neg_count / total

        if neg_ratio > 0.4:
            overall = "Negative"
            risk_val = min(95, int(neg_ratio * 100 + 20))
        elif pos_ratio > 0.5:
            overall = "Positive"
            risk_val = max(5, int(neg_ratio * 50))
        elif neg_ratio > 0.2:
            overall = "Mixed"
            risk_val = int(neg_ratio * 100 + 10)
        else:
            overall = "Neutral"
            risk_val = 15

        actions = []
        if risk_val >= 50:
            actions.append("CẢNH BÁO RỦI RO: Chuẩn bị thông cáo / FAQ phản hồi khiếu nại của khách hàng.")
            actions.append("Theo dõi sát các bài viết có tương tác cao (Top retweets/views).")
        else:
            actions.append("Tiếp tục theo dõi thảo luận định kỳ.")
            actions.append("Phản hồi tương tác tích cực để tăng nhận diện thương hiệu.")

        return {
            "tool": "analyze_sentiment",
            "query": query,
            "total_posts": len(items),
            "sentiment_breakdown": {
                "positive": pos_count,
                "negative": neg_count,
                "neutral": neu_count
            },
            "overall_sentiment": overall,
            "risk_score": f"{risk_val}%",
            "key_issues": list(issues) if issues else ["Trải nghiệm sử dụng", "Tính năng & Sản phẩm"],
            "recommended_actions": actions
        }
    except Exception as exc:
        return err("analyze_sentiment", exc)
